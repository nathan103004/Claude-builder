import asyncio
import json
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_create_session_returns_id():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/sessions", json={
            "postal_code": "H9K 1P9",
            "service_type": "Consultation urgente",
        })
    assert r.status_code == 201
    data = r.json()
    assert "session_id" in data
    assert isinstance(data["session_id"], str)
    # cleanup
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.delete(f"/sessions/{data['session_id']}")


@pytest.mark.asyncio
async def test_delete_session_returns_204():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create = await client.post("/sessions", json={
            "postal_code": "H9K 1P9",
            "service_type": "Consultation urgente",
        })
        session_id = create.json()["session_id"]
        r = await client.delete(f"/sessions/{session_id}")
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_delete_nonexistent_session_returns_404():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.delete("/sessions/does-not-exist")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_stream_delivers_clinic_event():
    """SSE generator yields a clinics event from the queue."""
    from routers.sessions import _sessions, _event_generator
    session_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()
    _sessions[session_id] = {
        "queue": queue,
        "task": None,
        "postal_code": "H9K 1P9",
        "service_type": "Consultation urgente",
    }
    clinics = [{"clinic_name": "Test", "address": "123 St", "slots": [{"date": "2026-04-05", "time": "09:30"}]}]
    await queue.put({"type": "clinics", "data": clinics})
    await queue.put(None)  # sentinel

    chunks = []
    async for chunk in _event_generator(session_id):
        chunks.append(chunk)

    _sessions.pop(session_id, None)
    combined = "".join(chunks)
    assert "event: clinics" in combined
    assert "Test" in combined


@pytest.mark.asyncio
async def test_stub_rvsq_returns_clinic_list():
    from routers.sessions import _stub_rvsq_search
    results = _stub_rvsq_search("H9K 1P9", "Consultation urgente")
    assert isinstance(results, list)
    assert len(results) > 0
    clinic = results[0]
    assert "clinic_name" in clinic
    assert "address" in clinic
    assert "slots" in clinic
    for slot in clinic["slots"]:
        assert "date" in slot
        assert "time" in slot
