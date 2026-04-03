import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
from main import app
from models.rvsq_models import RVSQError, ClinicCard, TimeSlot, BookingResult


CREDS_PAYLOAD = {
    "prenom": "Marie", "nom": "Tremblay",
    "numero_assurance_maladie": "TREM 1234 5678",
    "numero_sequentiel": "01",
    "date_naissance_jour": "15",
    "date_naissance_mois": "03",
    "date_naissance_annee": "1985",
}

SEARCH_PAYLOAD = {
    "session_id": "test-session",
    "code_postal": "H2X 1Y4",
    "service_type": "consultation_urgente",
    "date_debut": "2026-04-05",
}

BOOK_PAYLOAD = {
    "session_id": "test-session",
    "slot_id": "slot-abc",
}


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_login_success(client):
    async with client as c:
        with patch("routers.rvsq_router._login_sync", return_value="new-session-id"):
            resp = await c.post("/rvsq/login", json=CREDS_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json()["session_id"] == "new-session-id"


async def test_login_failure_returns_401(client):
    async with client as c:
        with patch("routers.rvsq_router._login_sync",
                   return_value=RVSQError(code="LOGIN_FAILED", message="bad creds")):
            resp = await c.post("/rvsq/login", json=CREDS_PAYLOAD)
    assert resp.status_code == 401


async def test_login_cloudflare_returns_503(client):
    async with client as c:
        with patch("routers.rvsq_router._login_sync",
                   return_value=RVSQError(code="CLOUDFLARE", message="blocked")):
            resp = await c.post("/rvsq/login", json=CREDS_PAYLOAD)
    assert resp.status_code == 503


async def test_search_success(client):
    clinic = ClinicCard(clinic_name="Clinique A", address="123 rue", slots=[
        TimeSlot(date="2026-04-05", time="09:30", slot_id="abc")
    ])
    async with client as c:
        with patch("routers.rvsq_router._get_valid_session", return_value=MagicMock()), \
             patch("routers.rvsq_router._search_sync", return_value=[clinic]):
            resp = await c.post("/rvsq/search", json=SEARCH_PAYLOAD)
    assert resp.status_code == 200
    assert len(resp.json()["clinics"]) == 1


async def test_search_session_not_found_returns_404(client):
    async with client as c:
        with patch("routers.rvsq_router._get_valid_session", return_value=None):
            resp = await c.post("/rvsq/search", json=SEARCH_PAYLOAD)
    assert resp.status_code == 404


async def test_book_success(client):
    result = BookingResult(
        confirmation_number="RV-001", clinic_name="Clinique A",
        slot_date="2026-04-05", slot_time="09:30"
    )
    async with client as c:
        with patch("routers.rvsq_router._get_valid_session", return_value=MagicMock()), \
             patch("routers.rvsq_router._book_sync", return_value=result):
            resp = await c.post("/rvsq/book", json=BOOK_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json()["confirmation_number"] == "RV-001"


async def test_book_slot_taken_returns_409(client):
    async with client as c:
        with patch("routers.rvsq_router._get_valid_session", return_value=MagicMock()), \
             patch("routers.rvsq_router._book_sync",
                   return_value=RVSQError(code="SLOT_TAKEN", message="taken")):
            resp = await c.post("/rvsq/book", json=BOOK_PAYLOAD)
    assert resp.status_code == 409


async def test_delete_session_returns_204(client):
    async with client as c:
        with patch("routers.rvsq_router.session_store") as mock_store:
            resp = await c.delete("/rvsq/session/some-id")
    assert resp.status_code == 204
