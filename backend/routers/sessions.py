from __future__ import annotations

import asyncio
import json
import uuid
from datetime import date, timedelta
from typing import AsyncIterator, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/sessions", tags=["sessions"])

# Polling timing constants
_POLL_INTERVAL = 5          # seconds between each search
_NO_RESULTS_TIMEOUT = 600   # seconds before pausing (10 minutes)
_PAUSE_DURATION = 3600      # seconds to pause before retrying (1 hour)
_PAUSE_ADVERTISED = 3600    # retry_in shown to clients — kept separate from _PAUSE_DURATION so tests can patch the sleep without changing what clients see

# session_id -> { queue, task, postal_code, service_type, user_email, notify }
_sessions: dict[str, dict] = {}


def _stub_rvsq_search(postal_code: str, service_type: str) -> list[dict]:
    """Return mock clinic cards. Replace body with real Selenium when issues #13-17 land."""
    today = date.today()
    return [
        {
            "clinic_name": "Clinique Saint-Laurent",
            "address": "1234 Boul. Saint-Laurent, Montréal, QC",
            "slots": [
                {"date": (today + timedelta(days=1)).isoformat(), "time": "09:30", "slot_id": "6676"},
                {"date": (today + timedelta(days=1)).isoformat(), "time": "14:00", "slot_id": "6676"},
                {"date": (today + timedelta(days=2)).isoformat(), "time": "10:00", "slot_id": "6676"},
            ],
        },
        {
            "clinic_name": "GMF-U Notre-Dame",
            "address": "1560 Rue Sherbrooke E, Montréal, QC",
            "slots": [
                {"date": (today + timedelta(days=1)).isoformat(), "time": "08:00", "slot_id": "1234"},
            ],
        },
    ]


async def _poll(session_id: str) -> None:
    no_results_elapsed = 0

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

            has_slots = any(slot for clinic in results for slot in clinic.get("slots", []))
            if has_slots:
                no_results_elapsed = 0
            else:
                no_results_elapsed += _POLL_INTERVAL
                if no_results_elapsed >= _NO_RESULTS_TIMEOUT:
                    await session["queue"].put({"type": "paused", "retry_in": _PAUSE_ADVERTISED})
                    try:
                        await asyncio.sleep(_PAUSE_DURATION)
                    except asyncio.CancelledError:
                        break
                    no_results_elapsed = 0
                    continue

        except Exception:
            await session["queue"].put({"type": "error", "retry_in": 300})

        try:
            await asyncio.sleep(_POLL_INTERVAL)
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
    token: Optional[str] = None


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
        "user_email": None,
        "notify": False,
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
