import asyncio
import json
import logging
import uuid
from datetime import date, timedelta
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/sessions", tags=["sessions"])
_log = logging.getLogger(__name__)

# session_id -> { queue, task, postal_code, service_type }
_sessions: dict[str, dict] = {}


def _stub_rvsq_search(postal_code: str, service_type: str) -> list[dict]:
    """Return mock clinic cards. Replace body with real Selenium when issues #13-17 land."""
    today = date.today()
    return [
        {
            "clinic_name": "Clinique Saint-Laurent",
            "address": "1234 Boul. Saint-Laurent, Montréal, QC",
            "slots": [
                {"date": (today + timedelta(days=1)).isoformat(), "time": "09:30"},
                {"date": (today + timedelta(days=1)).isoformat(), "time": "14:00"},
                {"date": (today + timedelta(days=2)).isoformat(), "time": "10:00"},
            ],
        },
        {
            "clinic_name": "GMF-U Notre-Dame",
            "address": "1560 Rue Sherbrooke E, Montréal, QC",
            "slots": [
                {"date": (today + timedelta(days=1)).isoformat(), "time": "08:00"},
            ],
        },
    ]


async def _poll(session_id: str) -> None:
    interval = 300    # 5 min
    max_interval = 1800  # 30 min

    while session_id in _sessions:
        session = _sessions[session_id]
        try:
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                _stub_rvsq_search,
                session["postal_code"],
                session["service_type"],
            )
            await session["queue"].put({"type": "clinics", "data": results})
            _log.debug("New results for session %s — would email if opted in", session_id)
            interval = 300
        except Exception:
            interval = min(interval * 2, max_interval)
            await session["queue"].put({"type": "error", "retry_in": interval})

        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            break


async def _event_generator(session_id: str) -> AsyncIterator[str]:
    session = _sessions.get(session_id)
    if not session:
        return

    queue: asyncio.Queue = session["queue"]
    while True:
        try:
            item = await asyncio.wait_for(queue.get(), timeout=25)
        except asyncio.TimeoutError:
            yield ": keepalive\n\n"
            continue

        if item is None:
            break

        event_type = item.get("type", "clinics")
        yield f"event: {event_type}\ndata: {json.dumps(item)}\n\n"


class SessionRequest(BaseModel):
    postal_code: str
    service_type: str = "Consultation urgente"


@router.post("", status_code=201)
async def create_session(body: SessionRequest):
    session_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()
    task = asyncio.create_task(_poll(session_id))
    _sessions[session_id] = {
        "queue": queue,
        "task": task,
        "postal_code": body.postal_code,
        "service_type": body.service_type,
    }
    return {"session_id": session_id}


@router.get("/{session_id}/stream")
async def stream_session(session_id: str):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return StreamingResponse(
        _event_generator(session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: str):
    session = _sessions.pop(session_id, None)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    task = session.get("task")
    if task and not task.done():
        task.cancel()
    await session["queue"].put(None)
