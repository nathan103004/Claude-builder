from __future__ import annotations
from dataclasses import dataclass, field
from typing import TypedDict

# --- Input models ---

@dataclass
class RAMQCredentials:
    prenom: str
    nom: str
    numero_assurance_maladie: str   # e.g. "ABCD 1234 5678"
    numero_sequentiel: str          # e.g. "01"
    date_naissance_jour: str        # "15"
    date_naissance_mois: str        # "03"
    date_naissance_annee: str       # "1985"

@dataclass
class SearchParams:
    code_postal: str
    service_type: str               # key from SERVICE_TYPE_MAP
    date_debut: str                 # "YYYY-MM-DD"
    rayon_km: int = 50
    moments: list[str] = field(default_factory=lambda: ["avant-midi", "apres-midi", "soir"])

# --- Domain models ---

@dataclass
class TimeSlot:
    date: str
    time: str
    slot_id: str        # data-companyid from clinic card — identifies which clinic to click
    slot_data_ids: str = ""  # data-ids from button.h-TimeButton — identifies specific time slot

@dataclass
class ClinicCard:
    clinic_name: str
    address: str
    slots: list[TimeSlot]

@dataclass
class BookingResult:
    confirmation_number: str
    clinic_name: str
    slot_date: str
    slot_time: str

@dataclass
class RVSQError:
    code: str   # see ERROR_TO_STATUS below
    message: str

# --- Service type mapping ---

SERVICE_TYPE_MAP: dict[str, str] = {
    "consultation_urgente":      "Consultation urgente",
    "consultation_semi_urgente": "Consultation semi-urgente",
    "suivi":                     "Suivi",
    "suivi_pediatrique":         "Suivi pédiatrique",
    "suivi_grossesse":           "Suivi de grossesse",
}

# --- HTTP status mapping ---

ERROR_TO_STATUS: dict[str, int] = {
    "LOGIN_FAILED":         401,
    "SESSION_EXPIRED":      401,
    "CLOUDFLARE":           503,
    "SLOT_TAKEN":           409,
    "NO_RESULTS":           404,
    "BOOKING_FAILED":       500,
    "INVALID_SERVICE_TYPE": 422,
}

# --- API wire TypedDicts ---

class LoginResponse(TypedDict):
    session_id: str

class SearchResponse(TypedDict):
    clinics: list[dict]

class BookingResponse(TypedDict):
    confirmation_number: str
    clinic_name: str
    slot_date: str
    slot_time: str

class ErrorResponse(TypedDict):
    error_code: str
    message: str
