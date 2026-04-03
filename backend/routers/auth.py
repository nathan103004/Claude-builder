import json
import os
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt as _bcrypt

from fastapi import APIRouter, HTTPException
from jose import jwt
from pydantic import BaseModel, EmailStr

USERS_FILE = os.path.join(os.path.dirname(__file__), '..', 'users.json')
SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 30

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRequest(BaseModel):
    email: EmailStr
    password: str


def _read_users() -> list[dict]:
    with open(USERS_FILE) as f:
        return json.load(f)


def _write_users(users: list[dict]) -> None:
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)


def _make_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/register", status_code=201)
def register(body: AuthRequest):
    users = _read_users()
    if any(u["email"] == body.email for u in users):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = {
        "id": str(uuid.uuid4()),
        "email": body.email,
        "password_hash": _bcrypt.hashpw(body.password.encode(), _bcrypt.gensalt()).decode(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    users.append(user)
    _write_users(users)
    return {"token": _make_token(user["id"])}


@router.post("/login")
def login(body: AuthRequest):
    users = _read_users()
    user = next((u for u in users if u["email"] == body.email), None)
    if not user or not _bcrypt.checkpw(body.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": _make_token(user["id"])}
