from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from models.rvsq_models import RAMQCredentials, RVSQError
from selenium_runner import navigate_to_rvsq

# --- Selectors (update with real values from DevTools inspection of RVSQ portal) ---
LOGIN_PRENOM_ID      = "REPLACE_WITH_REAL_ID"
LOGIN_NOM_ID         = "REPLACE_WITH_REAL_ID"
LOGIN_RAMQ_ID        = "REPLACE_WITH_REAL_ID"
LOGIN_SEQ_ID         = "REPLACE_WITH_REAL_ID"
LOGIN_JOUR_ID        = "REPLACE_WITH_REAL_ID"
LOGIN_MOIS_ID        = "REPLACE_WITH_REAL_ID"
LOGIN_ANNEE_ID       = "REPLACE_WITH_REAL_ID"
LOGIN_CONSENT_ID     = "REPLACE_WITH_REAL_ID"
LOGIN_SUBMIT_ID      = "REPLACE_WITH_REAL_ID"
LOGIN_ERROR_SELECTOR = "REPLACE_WITH_REAL_CSS_SELECTOR"
POST_LOGIN_SELECTOR  = "REPLACE_WITH_REAL_CSS_SELECTOR"

FIELD_ORDER = [
    LOGIN_PRENOM_ID, LOGIN_NOM_ID, LOGIN_RAMQ_ID,
    LOGIN_SEQ_ID, LOGIN_JOUR_ID, LOGIN_MOIS_ID, LOGIN_ANNEE_ID,
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


def login_rvsq(driver: webdriver.Chrome, credentials: RAMQCredentials) -> None | RVSQError:
    try:
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
            credentials.date_naissance_mois,
            credentials.date_naissance_annee,
        ]
        for field_id, value in zip(FIELD_ORDER, field_values):
            el = driver.find_element(By.ID, field_id)
            el.clear()
            el.send_keys(value)

        consent = _find_consent_checkbox(driver)
        if not consent.is_selected():
            consent.click()

        _find_submit_button(driver).click()

        if not _wait_for_post_login(driver):
            return RVSQError(code="LOGIN_FAILED", message="Invalid RAMQ credentials.")

        return None

    except WebDriverException as e:
        return RVSQError(code="LOGIN_FAILED", message=str(e))
