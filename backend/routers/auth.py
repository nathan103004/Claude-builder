from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt as _bcrypt

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr

USERS_FILE = os.path.join(os.path.dirname(__file__), '..', 'users.json')
SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 30

_bearer = HTTPBearer(auto_error=False)


def _decode_token(credentials: Optional[HTTPAuthorizationCredentials]) -> Optional[str]:
    """Return user_id from a valid Bearer token, or None."""
    if credentials is None:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRequest(BaseModel):
    email: EmailStr
    password: str
    email_notifications: bool = False


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
        "email_notifications": body.email_notifications,
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


class PreferencesRequest(BaseModel):
    email_notifications: bool


@router.patch("/me/preferences")
def update_preferences(
    body: PreferencesRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
):
    user_id = _decode_token(credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    users = _read_users()
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["email_notifications"] = body.email_notifications
    _write_users(users)
    return {"email_notifications": user["email_notifications"]}
