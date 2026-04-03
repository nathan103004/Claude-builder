import json
import os
import pytest
from httpx import AsyncClient, ASGITransport
from main import app

USERS_FILE = os.path.join(os.path.dirname(__file__), '..', 'users.json')


@pytest.fixture(autouse=True)
def reset_users():
    with open(USERS_FILE, 'w') as f:
        json.dump([], f)
    yield
    with open(USERS_FILE, 'w') as f:
        json.dump([], f)


@pytest.mark.asyncio
async def test_register_returns_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/auth/register", json={"email": "a@b.com", "password": "Pass1!"})
    assert r.status_code == 201
    assert "token" in r.json()
    assert len(r.json()["token"]) > 20


@pytest.mark.asyncio
async def test_register_hashes_password():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/auth/register", json={"email": "c@d.com", "password": "Pass1!"})
    users = json.loads(open(USERS_FILE).read())
    assert users[0]["password_hash"] != "Pass1!"
    assert users[0]["email"] == "c@d.com"


@pytest.mark.asyncio
async def test_register_duplicate_returns_409():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/auth/register", json={"email": "dup@x.com", "password": "Pass1!"})
        r = await client.post("/auth/register", json={"email": "dup@x.com", "password": "Pass1!"})
    assert r.status_code == 409
    assert r.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_login_valid_credentials():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/auth/register", json={"email": "e@f.com", "password": "Pass1!"})
        r = await client.post("/auth/login", json={"email": "e@f.com", "password": "Pass1!"})
    assert r.status_code == 200
    assert "token" in r.json()


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/auth/register", json={"email": "g@h.com", "password": "Pass1!"})
        r = await client.post("/auth/login", json={"email": "g@h.com", "password": "Wrong!"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_login_unknown_email_returns_401():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/auth/login", json={"email": "nobody@x.com", "password": "Pass1!"})
    assert r.status_code == 401
