from __future__ import annotations

import sys
import types
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch

from main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _async_gen(items):
    for item in items:
        yield item


def make_mock_stream(text_deltas):
    """Return an async context manager whose text_stream yields text_deltas."""
    mock_stream = MagicMock()
    mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
    mock_stream.__aexit__ = AsyncMock(return_value=False)
    mock_stream.text_stream = _async_gen(text_deltas)
    return mock_stream


def _make_anthropic_module(instance):
    """Build a fake 'anthropic' module whose AsyncAnthropic() returns instance."""
    mock_cls = MagicMock(return_value=instance)
    fake_module = types.ModuleType("anthropic")
    fake_module.AsyncAnthropic = mock_cls
    return fake_module, mock_cls


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_chat_returns_503_without_api_key(client, monkeypatch):
    """Endpoint raises 503 when ANTHROPIC_API_KEY is not set."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    async with client as c:
        resp = await c.post("/chat", json={
            "messages": [{"role": "user", "content": "hello"}],
            "locale": "en",
        })
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_chat_streams_tokens(client, monkeypatch):
    """SSE response contains event: token lines for each text delta."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    mock_instance = MagicMock()
    mock_instance.messages.stream.return_value = make_mock_stream(["Hello ", "there"])
    fake_mod, _ = _make_anthropic_module(mock_instance)

    with patch.dict(sys.modules, {"anthropic": fake_mod}):
        async with client as c:
            resp = await c.post("/chat", json={
                "messages": [{"role": "user", "content": "headache"}],
                "locale": "en",
            })

    body = resp.text
    assert "event: token" in body
    assert "Hello " in body
    assert "there" in body


@pytest.mark.asyncio
async def test_chat_emits_result_event_when_json_in_response(client, monkeypatch):
    """When Claude returns JSON with service_type, SSE includes event: result."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    response_text = '{"service_type": "suivi", "explanation": "routine checkup"}'

    mock_instance = MagicMock()
    mock_instance.messages.stream.return_value = make_mock_stream([response_text])
    fake_mod, _ = _make_anthropic_module(mock_instance)

    with patch.dict(sys.modules, {"anthropic": fake_mod}):
        async with client as c:
            resp = await c.post("/chat", json={
                "messages": [{"role": "user", "content": "regular checkup"}],
                "locale": "en",
            })

    body = resp.text
    assert "event: result" in body
    assert "suivi" in body


@pytest.mark.asyncio
async def test_emergency_response_emits_emergency_result(client, monkeypatch):
    """When Claude returns emergency service_type, SSE event: result contains it."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    response_text = '{"service_type": "emergency", "explanation": "chest pain"}'

    mock_instance = MagicMock()
    mock_instance.messages.stream.return_value = make_mock_stream([response_text])
    fake_mod, _ = _make_anthropic_module(mock_instance)

    with patch.dict(sys.modules, {"anthropic": fake_mod}):
        async with client as c:
            resp = await c.post("/chat", json={
                "messages": [{"role": "user", "content": "severe chest pain"}],
                "locale": "en",
            })

    body = resp.text
    assert "event: result" in body
    assert "emergency" in body


@pytest.mark.asyncio
async def test_final_turn_directive_added_after_two_user_turns(monkeypatch):
    """_stream_chat appends the final directive when >= 2 user messages are present."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    from routers.chat import _stream_chat, ChatMessage, FINAL_DIRECTIVES

    captured_system: list[str] = []
    mock_instance = MagicMock()

    def capturing_stream(**kwargs):
        captured_system.append(kwargs.get("system", ""))
        return make_mock_stream(["ok"])

    mock_instance.messages.stream.side_effect = capturing_stream
    fake_mod, _ = _make_anthropic_module(mock_instance)

    with patch.dict(sys.modules, {"anthropic": fake_mod}):
        messages = [
            ChatMessage(role="user", content="first message"),
            ChatMessage(role="assistant", content="any reply"),
            ChatMessage(role="user", content="second message"),
        ]

        # Consume the async generator to completion
        async for _ in _stream_chat(messages, "en"):
            pass

    assert len(captured_system) == 1
    assert FINAL_DIRECTIVES["en"] in captured_system[0]
