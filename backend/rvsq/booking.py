from __future__ import annotations
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from models.rvsq_models import BookingResult, RVSQError

# --- Selectors confirmed from live RVSQ DOM inspection ---
#
# Full booking flow (5 steps):
#   1. Results page: click a.h-selectClinic[data-companyid=X]
#   2. Calendar page: wait for button.h-TimeButton, click first slot
#   3. Contact-info form: fill email/phone, click .buttonContinueCIF
#   4. Summary page: click .buttonConfirmAppointment
#   5. Confirmation page: read reference number from input.noReferenceAssure[value]
#
# Error states:
#   Session expired: .WarningMessage_ExpiredNAM

# Confirmed selectors (all verified from live RVSQ DOM inspection)
CLINIC_CARD_CSS      = "a.h-selectClinic[data-companyid='{company_id}']"  # slot_id = data-companyid
CALENDAR_PAGE_CSS    = "button.h-TimeButton"              # confirms we're on slot calendar page
SLOT_TIME_BUTTON_CSS = "button.h-TimeButton"              # individual time slot button
CONTINUE_BUTTON_CSS  = ".buttonContinueCIF"               # "Continuer" on contact-info form
CONFIRM_BUTTON_CSS   = ".buttonConfirmAppointment"        # "Confirmer le rendez-vous" on summary page
CONFIRM_NUMBER_CSS   = "input.noReferenceAssure"          # hidden input, value = reference number (no spaces)
SLOT_TAKEN_CSS       = ".alert.alert-danger"              # generic danger alert
SESSION_EXPIRED_CSS  = ".WarningMessage_ExpiredNAM"       # confirmed from inspect_rvsq.py

WAIT_TIMEOUT = 15


def _locate_and_click_slot(
    driver: webdriver.Chrome,
    slot_id: str,
    email: str = "",
    phone: str = "",
) -> None:
    """
    Full booking navigation flow:
    1. Click the clinic card (a.h-selectClinic[data-companyid=slot_id])
    2. Wait for the slot calendar page (button.h-TimeButton visible)
    3. Click the first available time slot button
    4. Fill contact info (email, phone) and click "Continuer"
    5. Click "Confirmer le rendez-vous" on the summary page
    """
    # Step 1 — click clinic card
    selector = CLINIC_CARD_CSS.replace("{company_id}", slot_id)
    el = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
    )
    el.click()

    # Step 2 — wait for calendar page (at least one time slot button visible)
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, CALENDAR_PAGE_CSS))
    )

    # Step 3 — click first available time slot
    slot_el = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, SLOT_TIME_BUTTON_CSS))
    )
    slot_el.click()

    # Step 4 — contact info form: fill email/phone if provided, then click "Continuer"
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, CONTINUE_BUTTON_CSS))
    )
    if email:
        email_inputs = driver.find_elements(By.CSS_SELECTOR, "input.h-EmailTextBox")
        if email_inputs:
            email_inputs[0].clear()
            email_inputs[0].send_keys(email)
    if phone:
        phone_inputs = driver.find_elements(By.CSS_SELECTOR, "input.CellNumber")
        if phone_inputs:
            phone_inputs[0].clear()
            phone_inputs[0].send_keys(phone)
    driver.find_element(By.CSS_SELECTOR, CONTINUE_BUTTON_CSS).click()

    # Step 5 — summary page: click "Confirmer le rendez-vous"
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, CONFIRM_BUTTON_CSS))
    ).click()


def _wait_for_confirmation(driver: webdriver.Chrome) -> tuple | None:
    """Return (confirmation_number, clinic_name, date, time) or None if not found.

    The confirmation page contains a hidden input.noReferenceAssure whose value
    attribute holds the reference number without spaces (e.g. "4JJOWYKSIZD0").
    """
    try:
        el = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, CONFIRM_NUMBER_CSS))
        )
        number = el.get_attribute("value") or ""
        number = number.strip()
        return (number, "", "", "") if number else None
    except TimeoutException:
        return None


def _check_slot_taken(driver: webdriver.Chrome) -> bool:
    return len(driver.find_elements(By.CSS_SELECTOR, SLOT_TAKEN_CSS)) > 0


def _check_session_expired(driver: webdriver.Chrome) -> bool:
    return len(driver.find_elements(By.CSS_SELECTOR, SESSION_EXPIRED_CSS)) > 0


def _assert_selectors_configured() -> None:
    """All selectors are now confirmed — nothing to assert."""
    pass


def book_slot(
    driver: webdriver.Chrome,
    slot_id: str,
    email: str = "",
    phone: str = "",
) -> BookingResult | RVSQError:
    """
    slot_id = data-companyid from the clinic card (from ClinicCard.slots[n].slot_id).
    email/phone are filled into the contact-info form (step 4 of the RVSQ flow).
    Returns the reference number (e.g. "4JJOWYKSIZD0") on success.
    """
    try:
        _assert_selectors_configured()
        _locate_and_click_slot(driver, slot_id, email=email, phone=phone)
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
