from __future__ import annotations
import asyncio
import dataclasses
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.rvsq_models import (
    RAMQCredentials, SearchParams, RVSQError, ERROR_TO_STATUS,
    ClinicCard, BookingResult,
)
from rvsq import session_store
from rvsq.login import login_rvsq
from rvsq.search import search_clinics
from rvsq.booking import book_slot

router = APIRouter()


# --- Request models ---

class LoginRequest(BaseModel):
    prenom: str
    nom: str
    numero_assurance_maladie: str
    numero_sequentiel: str
    date_naissance_jour: str
    date_naissance_mois: str
    date_naissance_annee: str

class SearchRequest(BaseModel):
    session_id: str
    code_postal: str
    service_type: str
    date_debut: str
    rayon_km: int = 50
    moments: list[str] = ["avant-midi", "apres-midi", "soir"]

class BookRequest(BaseModel):
    session_id: str
    slot_id: str


# --- Helpers ---

def _raise_if_error(result: Any) -> None:
    if isinstance(result, RVSQError):
        status = ERROR_TO_STATUS.get(result.code, 500)
        raise HTTPException(status_code=status, detail={"error_code": result.code, "message": result.message})


def _get_valid_session(session_id: str):
    if not session_store.is_session_valid(session_id):
        return None
    return session_store.get_session(session_id)


def _to_dict(obj):
    return dataclasses.asdict(obj) if dataclasses.is_dataclass(obj) else obj


# --- Sync helpers (run in thread pool via asyncio.to_thread) ---

def _login_sync(credentials: RAMQCredentials) -> str | RVSQError:
    session_id = session_store.create_session(credentials)
    entry = session_store.get_session(session_id)
    error = login_rvsq(entry["driver"], credentials)
    if isinstance(error, RVSQError):
        session_store.delete_session(session_id)
        return error
    return session_id


def _search_sync(session_id: str, params: SearchParams) -> list[ClinicCard] | RVSQError:
    entry = session_store.get_session(session_id)
    result = search_clinics(entry["driver"], params)
    if not isinstance(result, RVSQError):
        session_store.touch_session(session_id)
    return result


def _book_sync(session_id: str, slot_id: str) -> BookingResult | RVSQError:
    entry = session_store.get_session(session_id)
    result = book_slot(entry["driver"], slot_id)
    if isinstance(result, RVSQError) and result.code == "SESSION_EXPIRED":
        reauth = session_store.reauth_session(session_id)
        if isinstance(reauth, RVSQError):
            return reauth
        entry = session_store.get_session(session_id)
        result = book_slot(entry["driver"], slot_id)
    if not isinstance(result, RVSQError):
        session_store.touch_session(session_id)
    return result


# --- Endpoints ---

@router.post("/login")
async def login(body: LoginRequest):
    credentials = RAMQCredentials(**body.model_dump())
    result = await asyncio.to_thread(_login_sync, credentials)
    _raise_if_error(result)
    return {"session_id": result}


@router.post("/search")
async def search(body: SearchRequest):
    entry = _get_valid_session(body.session_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Session not found.")
    params = SearchParams(
        code_postal=body.code_postal,
        service_type=body.service_type,
        date_debut=body.date_debut,
        rayon_km=body.rayon_km,
        moments=body.moments,
    )
    result = await asyncio.to_thread(_search_sync, body.session_id, params)
    _raise_if_error(result)
    return {"clinics": [_to_dict(c) for c in result]}


@router.post("/book")
async def book(body: BookRequest):
    entry = _get_valid_session(body.session_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Session not found.")
    result = await asyncio.to_thread(_book_sync, body.session_id, body.slot_id)
    _raise_if_error(result)
    return _to_dict(result)


@router.delete("/session/{session_id}", status_code=204)
async def delete_session(session_id: str):
    await asyncio.to_thread(session_store.delete_session, session_id)
