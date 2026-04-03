from __future__ import annotations
from bs4 import BeautifulSoup
from selenium import webdriver
from models.rvsq_models import ClinicCard, TimeSlot, RVSQError

# --- CSS selectors ---
# NOTE: These match synthetic test fixtures. Update to real RVSQ portal selectors
# after live DevTools inspection.
CARD_CSS       = "div.rvsq-clinic-card"
NAME_CSS       = "span.clinic-name"
ADDRESS_CSS    = "span.clinic-address"
SLOT_CSS       = "div.available-slot"
SLOT_DATE_ATTR = "data-date"
SLOT_TIME_ATTR = "data-time"
SLOT_ID_ATTR   = "data-slot-id"
NO_RESULTS_CSS = "div.no-results-message"


def parse_clinic_cards_from_html(html: str) -> list[ClinicCard] | RVSQError:
    soup = BeautifulSoup(html, "html.parser")
    if soup.select_one(NO_RESULTS_CSS):
        return RVSQError(code="NO_RESULTS", message="No clinics found for the given search.")

    cards = []
    for card_el in soup.select(CARD_CSS):
        name_el = card_el.select_one(NAME_CSS)
        addr_el = card_el.select_one(ADDRESS_CSS)
        clinic_name = name_el.get_text(strip=True) if name_el else ""
        address = addr_el.get_text(strip=True) if addr_el else ""

        slots = []
        for slot_el in card_el.select(SLOT_CSS):
            slots.append(TimeSlot(
                date=slot_el.get(SLOT_DATE_ATTR, ""),
                time=slot_el.get(SLOT_TIME_ATTR, ""),
                slot_id=slot_el.get(SLOT_ID_ATTR, ""),
            ))

        cards.append(ClinicCard(clinic_name=clinic_name, address=address, slots=slots))

    return cards


def parse_clinic_cards(driver: webdriver.Chrome) -> list[ClinicCard] | RVSQError:
    return parse_clinic_cards_from_html(driver.page_source)
