from __future__ import annotations
from bs4 import BeautifulSoup
from selenium import webdriver
from models.rvsq_models import ClinicCard, TimeSlot, RVSQError

# --- CSS selectors confirmed from live RVSQ DOM inspection (inspect_rvsq.py + DevTools) ---
#
# Search results page (#criteres_t3 → after clicking Rechercher):
#   Each clinic is rendered as <a class="h-selectClinic"> with data attributes:
#     data-companyid     — clinic ID (used to click into a clinic)
#     data-startdate     — ISO 8601 datetime of first available slot
#   Inside the anchor:
#     h2.clinic-title    — clinic name
#     .tmbWrapper p      — address lines (first <p> in the float:left wrapper)
#
# No individual slot buttons appear on the search results page.
# The data-startdate attribute gives the first available slot directly.
#
# Slot calendar page (#selection-heure_t3, after clicking a clinic card):
#   Slot buttons are TODO — need inspection when appointments are actually available.

CARD_CSS        = "a.h-selectClinic"          # each clinic card anchor
NAME_CSS        = "h2.clinic-title"            # clinic name inside the card
ADDRESS_CSS     = ".tmbWrapper p"              # first <p> inside the float:left tmbWrapper
NO_RESULTS_CSS  = "#clinicsWithNoDisponibilitiesContainer"  # confirmed via inspect_rvsq.py

# Slot calendar page selectors — TODO: inspect when a slot is available
# After clicking a clinic (a.h-selectClinic), the portal navigates to #selection-heure_t3.
# Individual time slot buttons have not been observed yet (no availability during inspection).
SLOT_BUTTON_CSS = "REPLACE_AFTER_SLOT_INSPECTION"  # e.g. button.h-SlotButton or similar


def parse_clinic_cards_from_html(html: str) -> list[ClinicCard] | RVSQError:
    soup = BeautifulSoup(html, "html.parser")

    if soup.select_one(NO_RESULTS_CSS):
        return RVSQError(code="NO_RESULTS", message="No clinics found for the given search.")

    cards = []
    for card_el in soup.select(CARD_CSS):
        name_el = card_el.select_one(NAME_CSS)
        clinic_name = name_el.get_text(strip=True) if name_el else ""

        # Address: first <p> inside the float:left tmbWrapper
        addr_el = card_el.select_one(ADDRESS_CSS)
        address = addr_el.get_text(" ", strip=True) if addr_el else ""

        # First available slot comes from data-startdate (ISO datetime, e.g. "2026-04-04T13:30:00-04:00")
        # Parse into date + time for the TimeSlot model
        company_id = card_el.get("data-companyid", "")
        start_date_raw = card_el.get("data-startdate", "")

        slots = []
        if start_date_raw:
            try:
                # e.g. "2026-04-04T13:30:00-04:00" → date="2026-04-04", time="13:30"
                dt_part = start_date_raw[:16]   # "2026-04-04T13:30"
                date_str, time_str = dt_part.split("T")
                slots.append(TimeSlot(
                    date=date_str,
                    time=time_str,
                    slot_id=company_id,  # used to click the right clinic card
                ))
            except (ValueError, IndexError):
                pass

        cards.append(ClinicCard(clinic_name=clinic_name, address=address, slots=slots))

    return cards


def parse_clinic_cards(driver: webdriver.Chrome) -> list[ClinicCard] | RVSQError:
    return parse_clinic_cards_from_html(driver.page_source)
