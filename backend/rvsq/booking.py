from __future__ import annotations
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from models.rvsq_models import BookingResult, RVSQError

# --- Selectors (update from browser inspection of RVSQ booking flow) ---
SLOT_BUTTON_CSS     = "REPLACE"   # e.g. "[data-slot-id='SLOT_ID']"
CONFIRM_PAGE_CSS    = "REPLACE"   # element present on confirmation page
CONFIRM_NUMBER_CSS  = "REPLACE"   # element containing confirmation number
SLOT_TAKEN_CSS      = "REPLACE"   # error element when slot is already taken
SESSION_EXPIRED_CSS = "REPLACE"   # element indicating session expiry

WAIT_TIMEOUT = 15


def _locate_and_click_slot(driver, slot_id):
    selector = SLOT_BUTTON_CSS.replace("SLOT_ID", slot_id)
    el = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
    )
    el.click()


def _wait_for_confirmation(driver) -> tuple | None:
    """Return (confirmation_number, clinic_name, date, time) or None if not found."""
    try:
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, CONFIRM_PAGE_CSS))
        )
    except TimeoutException:
        return None
    confirm_el = driver.find_element(By.CSS_SELECTOR, CONFIRM_NUMBER_CSS)
    number = confirm_el.get_attribute("textContent") or confirm_el.text
    return (number.strip(), "", "", "")


def _check_slot_taken(driver) -> bool:
    return len(driver.find_elements(By.CSS_SELECTOR, SLOT_TAKEN_CSS)) > 0


def _check_session_expired(driver) -> bool:
    return len(driver.find_elements(By.CSS_SELECTOR, SESSION_EXPIRED_CSS)) > 0


def book_slot(driver: webdriver.Chrome, slot_id: str) -> BookingResult | RVSQError:
    try:
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
        return RVSQError(code="BOOKING_FAILED", message="Booking failed for unknown reason.")
    except WebDriverException as e:
        return RVSQError(code="BOOKING_FAILED", message=str(e))
