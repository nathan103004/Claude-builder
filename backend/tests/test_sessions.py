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


@pytest.mark.asyncio
async def test_poll_uses_5s_interval(monkeypatch):
    """_poll sleeps for 5 seconds between successful polls (not 300)."""
    import uuid as _uuid
    from routers.sessions import _sessions, _poll

    sleep_calls = []
    original_sleep = asyncio.sleep

    async def tracking_sleep(seconds):
        sleep_calls.append(seconds)
        if seconds >= 10:
            # Don't actually wait long in tests
            return
        await original_sleep(seconds)

    monkeypatch.setattr(asyncio, "sleep", tracking_sleep)

    session_id = str(_uuid.uuid4())
    queue = asyncio.Queue()
    _sessions[session_id] = {
        "queue": queue, "task": None,
        "postal_code": "H9K 1P9", "service_type": "Consultation urgente",
        "user_email": None, "notify": False,
    }
    task = asyncio.create_task(_poll(session_id))
    await asyncio.sleep(0.2)
    _sessions.pop(session_id, None)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    # At least one sleep call should have been 5 seconds
    assert any(s == 5 for s in sleep_calls), f"Expected 5s sleep, got: {sleep_calls}"


@pytest.mark.asyncio
async def test_poll_sends_paused_event_after_no_results(monkeypatch):
    """After 10 minutes of no slots, _poll pushes a paused event."""
    import uuid as _uuid
    from routers import sessions as sessions_mod
    from routers.sessions import _sessions, _poll

    # Stub returns clinics with NO slots
    def empty_search(postal_code, service_type):
        return [{"clinic_name": "Clinique Test", "address": "123 Rue Test", "slots": []}]

    monkeypatch.setattr(sessions_mod, "_stub_rvsq_search", empty_search)

    # Make time advance fast: each 5s sleep counts as 601s worth of no-results time
    no_results_elapsed = 0
    original_sleep = asyncio.sleep

    async def fast_sleep(seconds):
        nonlocal no_results_elapsed
        if seconds == 5:
            no_results_elapsed += 601  # jump past the 600s threshold immediately
        elif seconds >= 3600:
            return  # skip the hour sleep
        else:
            await original_sleep(min(seconds, 0.01))

    monkeypatch.setattr(asyncio, "sleep", fast_sleep)

    # Patch the no_results tracking by directly manipulating the threshold
    # Instead, just patch _NO_RESULTS_TIMEOUT to 0 so it triggers immediately
    monkeypatch.setattr(sessions_mod, "_NO_RESULTS_TIMEOUT", 0)
    monkeypatch.setattr(sessions_mod, "_PAUSE_DURATION", 0)

    session_id = str(_uuid.uuid4())
    queue = asyncio.Queue()
    _sessions[session_id] = {
        "queue": queue, "task": None,
        "postal_code": "H9K 1P9", "service_type": "Consultation urgente",
        "user_email": None, "notify": False,
    }
    task = asyncio.create_task(_poll(session_id))
    await asyncio.sleep(0.3)
    _sessions.pop(session_id, None)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    # Collect all queued events
    events = []
    while not queue.empty():
        events.append(await queue.get())

    event_types = [e.get("type") for e in events]
    assert "paused" in event_types, f"Expected paused event, got: {event_types}"
    paused_event = next(e for e in events if e.get("type") == "paused")
    assert paused_event.get("retry_in") == 3600
