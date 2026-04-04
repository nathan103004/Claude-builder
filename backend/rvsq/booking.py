from __future__ import annotations
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from models.rvsq_models import BookingResult, RVSQError

# --- Selectors confirmed from live RVSQ DOM inspection ---
#
# Step 1 — Click clinic card on search results page:
#   Each clinic is <a class="h-selectClinic" data-companyid="XXXX">
#   slot_id passed to book_slot() is the data-companyid value.
#
# Step 2 — Slot calendar page (#selection-heure_t3):
#   Shows available slots by day. Individual slot buttons — TODO (not yet observed).
#   SLOT_TIME_BUTTON_CSS needs inspection when a slot is actually available.
#
# Step 3 — Confirm page:
#   "Confirmer le rendez-vous" button: class="buttonConfirmAppointment" (confirmed)
#   Confirmation number element — TODO (not yet observed; inspect after confirming a booking)
#
# Step 4 — Error states:
#   Session expired: .WarningMessage_ExpiredNAM (confirmed from inspect_rvsq.py)

# Confirmed selectors
CLINIC_CARD_CSS      = "a.h-selectClinic[data-companyid='{company_id}']"  # slot_id = data-companyid
CALENDAR_PAGE_CSS    = "#selection-heure_t3, .h-PreviousCalendarPage, .h-NextCalendarPage"  # confirms we're on slot calendar
CONFIRM_BUTTON_CSS   = ".buttonConfirmAppointment"  # confirmed from inspect_rvsq.py

# TODO selectors — need inspection when a slot is available
SLOT_TIME_BUTTON_CSS = "REPLACE_AFTER_SLOT_INSPECTION"   # individual time slot button on calendar page
CONFIRM_NUMBER_CSS   = "REPLACE_AFTER_BOOKING_INSPECTION" # element containing confirmation number
SLOT_TAKEN_CSS       = ".alert.alert-danger"              # generic danger alert (best available without live observation)
SESSION_EXPIRED_CSS  = ".WarningMessage_ExpiredNAM"       # confirmed from inspect_rvsq.py

WAIT_TIMEOUT = 15


def _locate_and_click_slot(driver: webdriver.Chrome, slot_id: str) -> None:
    """
    Full booking navigation flow:
    1. Click the clinic card (a.h-selectClinic[data-companyid=slot_id])
    2. Wait for the slot calendar page (#selection-heure_t3)
    3. Click a specific time slot button (TODO: real selector after inspection)
    4. Click "Confirmer le rendez-vous"
    """
    # Step 1 — click clinic card
    selector = CLINIC_CARD_CSS.replace("{company_id}", slot_id)
    el = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
    )
    el.click()

    # Step 2 — wait for calendar page
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, CALENDAR_PAGE_CSS))
    )

    # Step 3 — click time slot (selector TBD — inspect when slot is available)
    slot_el = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, SLOT_TIME_BUTTON_CSS))
    )
    slot_el.click()

    # Step 4 — confirm
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, CONFIRM_BUTTON_CSS))
    ).click()


def _wait_for_confirmation(driver: webdriver.Chrome) -> tuple | None:
    """Return (confirmation_number, clinic_name, date, time) or None if not found."""
    if CONFIRM_NUMBER_CSS == "REPLACE_AFTER_BOOKING_INSPECTION":
        return None
    try:
        el = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, CONFIRM_NUMBER_CSS))
        )
        number = (el.get_attribute("textContent") or el.text).strip()
        return (number, "", "", "") if number else None
    except TimeoutException:
        return None


def _check_slot_taken(driver: webdriver.Chrome) -> bool:
    return len(driver.find_elements(By.CSS_SELECTOR, SLOT_TAKEN_CSS)) > 0


def _check_session_expired(driver: webdriver.Chrome) -> bool:
    return len(driver.find_elements(By.CSS_SELECTOR, SESSION_EXPIRED_CSS)) > 0


def _assert_selectors_configured() -> None:
    placeholders = {"REPLACE_AFTER_SLOT_INSPECTION", "REPLACE_AFTER_BOOKING_INSPECTION"}
    unconfigured = [
        name for name, val in [
            ("SLOT_TIME_BUTTON_CSS", SLOT_TIME_BUTTON_CSS),
            ("CONFIRM_NUMBER_CSS", CONFIRM_NUMBER_CSS),
        ] if val in placeholders
    ]
    if unconfigured:
        raise NotImplementedError(
            f"rvsq/booking.py: These selectors need inspection when a slot is available: {unconfigured}"
        )


def book_slot(driver: webdriver.Chrome, slot_id: str) -> BookingResult | RVSQError:
    """
    slot_id = data-companyid from the clinic card (from ClinicCard.slots[n].slot_id).
    Clicks the clinic, waits for calendar, clicks the first available time slot,
    confirms, and returns the confirmation number.

    NOTE: SLOT_TIME_BUTTON_CSS and CONFIRM_NUMBER_CSS are still placeholders.
    Inspect the portal when a time slot is available to fill them in.
    """
    try:
        _assert_selectors_configured()
        _locate_and_click_slot(driver, slot_id)
        confirmation = _wait_for_confirmation(driver)
        if confirmation:
            number, clinic, date, time_ = confirmation
            return BookingResult(
                confirmation_number=number,
                clinic_name=clinic,
                slot_date=date,
                slot_time=time_,
            )
        if _check_slot_taken(driver):
            return RVSQError(code="SLOT_TAKEN", message="This slot was already taken.")
        if _check_session_expired(driver):
            return RVSQError(code="SESSION_EXPIRED", message="RVSQ session expired.")
        return RVSQError(code="BOOKING_FAILED", message="Booking failed — confirmation not found.")
    except WebDriverException as e:
        return RVSQError(code="BOOKING_FAILED", message=str(e))
