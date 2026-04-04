from __future__ import annotations
from bs4 import BeautifulSoup
from selenium import webdriver
from models.rvsq_models import ClinicCard, TimeSlot, RVSQError

# --- CSS selectors ---
# CARD_CSS and slot selectors are synthetic test placeholders.
# To populate them: run inspect_rvsq.py, log in, run a search that RETURNS RESULTS,
# press Enter, then inspect the search_results_page section of rvsq_elements.json
# for the real clinic card container and slot button class/attribute names.
# The no-results selector is confirmed from live inspection.
CARD_CSS       = "div.rvsq-clinic-card"       # TODO: replace with real RVSQ class
NAME_CSS       = "span.clinic-name"            # TODO: replace with real RVSQ class
ADDRESS_CSS    = "span.clinic-address"         # TODO: replace with real RVSQ class
SLOT_CSS       = "div.available-slot"          # TODO: replace with real RVSQ class
SLOT_DATE_ATTR = "data-date"                   # TODO: confirm real attribute name
SLOT_TIME_ATTR = "data-time"                   # TODO: confirm real attribute name
SLOT_ID_ATTR   = "data-slot-id"               # TODO: confirm real attribute name
NO_RESULTS_CSS = "#clinicsWithNoDisponibilitiesContainer"  # confirmed via inspect_rvsq.py


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
