"""
Demo router — returns fake clinic data and simulates a booking confirmation.
No Selenium, no RAMQ credentials required.
Mounted at /demo (see main.py).
"""
from __future__ import annotations

import random
import string
from datetime import date, timedelta

from fastapi import APIRouter

router = APIRouter()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_ref() -> str:
    """Generate a realistic-looking RVSQ confirmation code (12 alphanumeric chars)."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=12))


def _upcoming_slots(company_id: str, count: int) -> list[dict]:
    """Return `count` daily slots starting from tomorrow."""
    today = date.today()
    slots = []
    for i in range(1, count + 1):
        d = today + timedelta(days=i)
        slots.append({
            "date": d.isoformat(),
            "time": f"{9 + i}:00",
            "slot_id": company_id,
        })
    return slots


# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

DEMO_CLINICS = [
    {
        "clinic_name": "Clinique médicale Côte-des-Neiges (DÉMO)",
        "address": "5700 Chemin de la Côte-des-Neiges, Montréal, QC H3T 2A8",
        "slots": _upcoming_slots("demo-clinic-001", 3),
    },
    {
        "clinic_name": "Clinique Plateau-Mont-Royal (DÉMO)",
        "address": "4235 Avenue du Parc, Montréal, QC H2W 2H2",
        "slots": _upcoming_slots("demo-clinic-002", 2),
    },
    {
        "clinic_name": "GMF-Réseau Rosemont (DÉMO)",
        "address": "2924 Rue Beaubien E, Montréal, QC H1Y 1G2",
        "slots": _upcoming_slots("demo-clinic-003", 1),
    },
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/clinics")
def demo_clinics():
    """Return fake clinic cards for demo mode (no login required)."""
    return {"clinics": DEMO_CLINICS}


class BookDemoRequest:
    pass


from pydantic import BaseModel

class DemoBookRequest(BaseModel):
    slot_id: str
    clinic_name: str = ""
    slot_date: str = ""
    slot_time: str = ""


@router.post("/book")
def demo_book(body: DemoBookRequest):
    """Simulate a booking and return a fake confirmation number."""
    return {
        "confirmation_number": _fake_ref(),
        "clinic_name": body.clinic_name,
        "slot_date": body.slot_date,
        "slot_time": body.slot_time,
    }
