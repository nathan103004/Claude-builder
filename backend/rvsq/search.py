from __future__ import annotations
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from models.rvsq_models import SearchParams, ClinicCard, RVSQError, SERVICE_TYPE_MAP
from rvsq.scraper import parse_clinic_cards

# --- Selectors (populated from rvsq_elements.json DOM inspection via inspect_rvsq.py) ---
# Recherche.aspx uses hash fragments: #accueil (post-login landing) → #criteres_t1 (search form)
SEARCH_NAV_SELECTOR    = 'a[href="#criteres_t1"]'
POSTAL_CODE_ID         = "PostalCode"
RADIUS_SELECT_ID       = "perimeterCombo"   # options text: "10 km"…"50 km"
DATE_ID                = "DateRangeStart"   # flatpickr date input, format jj-mm-aaaa (DD-MM-YYYY)
SERVICE_TYPE_SELECT_ID = "consultingReason" # options: "Consultation urgente", "Suivi", etc.
SEARCH_BUTTON_ID       = "searchbutton"
# #assure-next-btn (calendar navigation) is rendered only when results are present
RESULTS_CONTAINER_CSS  = "#assure-next-btn"
# Shown when zero clinics matched the search criteria
NO_RESULTS_CSS         = "#clinicsWithNoDisponibilitiesContainer"

MOMENTS = {
    "avant-midi": "chkMatin",
    "apres-midi": "chkPm",
    "soir":       "chkSoir",
}

WAIT_TIMEOUT = 15


def _navigate_to_search_form(driver):
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, SEARCH_NAV_SELECTOR))
    ).click()


def _fill_postal_code(driver, code_postal):
    el = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.ID, POSTAL_CODE_ID))
    )
    el.clear()
    el.send_keys(code_postal)


def _set_radius(driver, rayon_km):
    # Option visible text is "10 km", "20 km", etc. — use visible text, not value attribute
    Select(driver.find_element(By.ID, RADIUS_SELECT_ID)).select_by_visible_text(f"{rayon_km} km")


def _set_date(driver, date_debut):
    el = driver.find_element(By.ID, DATE_ID)
    el.clear()
    el.send_keys(date_debut)


def _set_moments(driver, moments):
    for key, checkbox_id in MOMENTS.items():
        checkbox = driver.find_element(By.ID, checkbox_id)
        if key in moments and not checkbox.is_selected():
            checkbox.click()
        elif key not in moments and checkbox.is_selected():
            checkbox.click()


def _set_service_type(driver, service_type_label):
    Select(driver.find_element(By.ID, SERVICE_TYPE_SELECT_ID)).select_by_visible_text(service_type_label)


def _click_search(driver):
    driver.find_element(By.ID, SEARCH_BUTTON_ID).click()


def _wait_for_results(driver):
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.any_of(
            EC.presence_of_element_located((By.CSS_SELECTOR, RESULTS_CONTAINER_CSS)),
            EC.presence_of_element_located((By.CSS_SELECTOR, NO_RESULTS_CSS)),
        )
    )


def _assert_selectors_configured() -> None:
    # All search form selectors are populated. No-op unless someone reverts to a placeholder.
    placeholders = {"REPLACE", "REPLACE_CHECKBOX_ID"}
    unconfigured = [
        name for name, val in [
            ("SEARCH_NAV_SELECTOR", SEARCH_NAV_SELECTOR),
            ("POSTAL_CODE_ID", POSTAL_CODE_ID),
            ("RADIUS_SELECT_ID", RADIUS_SELECT_ID),
            ("DATE_ID", DATE_ID),
            ("SERVICE_TYPE_SELECT_ID", SERVICE_TYPE_SELECT_ID),
            ("SEARCH_BUTTON_ID", SEARCH_BUTTON_ID),
            ("RESULTS_CONTAINER_CSS", RESULTS_CONTAINER_CSS),
            ("NO_RESULTS_CSS", NO_RESULTS_CSS),
            *[(f"MOMENTS[{k}]", v) for k, v in MOMENTS.items()],
        ] if val in placeholders
    ]
    if unconfigured:
        raise NotImplementedError(
            f"rvsq/search.py: These DOM selectors need real values from RVSQ DevTools inspection: {unconfigured}"
        )


def search_clinics(driver: webdriver.Chrome, params: SearchParams) -> list[ClinicCard] | RVSQError:
    if params.service_type not in SERVICE_TYPE_MAP:
        return RVSQError(code="INVALID_SERVICE_TYPE", message=f"Unknown service type: {params.service_type}")

    try:
        _assert_selectors_configured()
        _navigate_to_search_form(driver)
        _fill_postal_code(driver, params.code_postal)
        _set_radius(driver, params.rayon_km)
        _set_date(driver, params.date_debut)
        _set_moments(driver, params.moments)
        _set_service_type(driver, SERVICE_TYPE_MAP[params.service_type])
        _click_search(driver)
        _wait_for_results(driver)
        return parse_clinic_cards(driver)
    except WebDriverException as e:
        return RVSQError(code="SESSION_EXPIRED", message=str(e))
