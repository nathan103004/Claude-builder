from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from models.rvsq_models import RAMQCredentials, RVSQError
from selenium_runner import navigate_to_rvsq

# --- Selectors (populated from rvsq_elements.json DOM inspection) ---
LOGIN_PRENOM_ID      = "ctl00_ContentPlaceHolderMP_AssureForm_FirstName"
LOGIN_NOM_ID         = "ctl00_ContentPlaceHolderMP_AssureForm_LastName"
LOGIN_RAMQ_ID        = "ctl00_ContentPlaceHolderMP_AssureForm_NAM"
LOGIN_SEQ_ID         = "ctl00_ContentPlaceHolderMP_AssureForm_CardSeqNumber"
LOGIN_JOUR_ID        = "ctl00_ContentPlaceHolderMP_AssureForm_Day"
# Month is a <select>; Selenium Select is used separately — see _fill_month()
LOGIN_MOIS_ID        = "ctl00_ContentPlaceHolderMP_AssureForm_Month"
LOGIN_ANNEE_ID       = "ctl00_ContentPlaceHolderMP_AssureForm_Year"
LOGIN_CONSENT_ID     = "AssureForm_CSTMT"
LOGIN_SUBMIT_ID      = "ctl00_ContentPlaceHolderMP_myButton"
# Multiple possible error divs — any .alert element on the login page is an error
LOGIN_ERROR_SELECTOR = ".alert.ErrorMessage_ServicesAccessDenied, .alert.ErrorMessage_CaptchaInvalid, .alert.ErrorMessage_FillAllFields, .alert.ErrorMessage_InvalideDateformat"
# TODO: run inspect_rvsq.py after login to capture post-login selectors
POST_LOGIN_SELECTOR  = "REPLACE_WITH_REAL_CSS_SELECTOR"

# Text fields filled via send_keys (excludes month which is a <select>)
FIELD_ORDER = [
    LOGIN_PRENOM_ID, LOGIN_NOM_ID, LOGIN_RAMQ_ID,
    LOGIN_SEQ_ID, LOGIN_JOUR_ID, LOGIN_ANNEE_ID,
]

# RVSQ month option texts (French full names, 1-indexed)
_MONTH_NAMES = [
    "", "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]

WAIT_TIMEOUT = 15


def _wait_for_form(driver: webdriver.Chrome) -> None:
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.ID, LOGIN_PRENOM_ID))
    )


def _find_consent_checkbox(driver: webdriver.Chrome):
    return driver.find_element(By.ID, LOGIN_CONSENT_ID)


def _find_submit_button(driver: webdriver.Chrome):
    return driver.find_element(By.ID, LOGIN_SUBMIT_ID)


def _wait_for_post_login(driver: webdriver.Chrome) -> bool:
    """Return True if post-login success element appears; False on login failure."""
    try:
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, POST_LOGIN_SELECTOR)),
                EC.presence_of_element_located((By.CSS_SELECTOR, LOGIN_ERROR_SELECTOR)),
            )
        )
    except TimeoutException:
        return False
    error_els = driver.find_elements(By.CSS_SELECTOR, LOGIN_ERROR_SELECTOR)
    return len(error_els) == 0


def _assert_selectors_configured() -> None:
    """Raise NotImplementedError if any selector is still a placeholder."""
    placeholders = {"REPLACE_WITH_REAL_ID", "REPLACE_WITH_REAL_CSS_SELECTOR"}
    unconfigured = [
        name for name, val in [
            ("POST_LOGIN_SELECTOR", POST_LOGIN_SELECTOR),
        ] if val in placeholders
    ]
    if unconfigured:
        raise NotImplementedError(
            f"rvsq/login.py: These DOM selectors need real values from RVSQ DevTools inspection: {unconfigured}"
            "\n  Run inspect_rvsq.py → log in manually → press Enter → check rvsq_elements.json"
        )


def login_rvsq(driver: webdriver.Chrome, credentials: RAMQCredentials) -> None | RVSQError:
    try:
        _assert_selectors_configured()
        title = navigate_to_rvsq(driver)
        if "just a moment" in title.lower():
            return RVSQError(code="CLOUDFLARE", message="RVSQ portal blocked by Cloudflare challenge.")

        _wait_for_form(driver)

        field_values = [
            credentials.prenom,
            credentials.nom,
            credentials.numero_assurance_maladie,
            credentials.numero_sequentiel,
            credentials.date_naissance_jour,
            credentials.date_naissance_annee,
        ]
        for field_id, value in zip(FIELD_ORDER, field_values):
            el = driver.find_element(By.ID, field_id)
            el.clear()
            el.send_keys(value)

        # Month is a <select> — select by French month name
        month_num = int(credentials.date_naissance_mois)
        month_text = _MONTH_NAMES[month_num]
        Select(driver.find_element(By.ID, LOGIN_MOIS_ID)).select_by_visible_text(month_text)

        consent = _find_consent_checkbox(driver)
        if not consent.is_selected():
            consent.click()

        _find_submit_button(driver).click()

        if not _wait_for_post_login(driver):
            return RVSQError(code="LOGIN_FAILED", message="Invalid RAMQ credentials.")

        return None

    except WebDriverException as e:
        return RVSQError(code="LOGIN_FAILED", message=str(e))
