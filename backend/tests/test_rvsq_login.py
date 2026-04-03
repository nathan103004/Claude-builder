from unittest.mock import MagicMock, patch, call
import pytest
from models.rvsq_models import RAMQCredentials, RVSQError


def _creds():
    return RAMQCredentials(
        prenom="Marie", nom="Tremblay",
        numero_assurance_maladie="TREM 1234 5678",
        numero_sequentiel="01",
        date_naissance_jour="15",
        date_naissance_mois="03",
        date_naissance_annee="1985",
    )


def _mock_driver(post_login_has_error=False, post_login_has_success=True):
    driver = MagicMock()
    element = MagicMock()
    driver.find_element.return_value = element
    driver.find_elements.return_value = [element] if post_login_has_error else []
    return driver


def test_login_calls_navigate_to_rvsq():
    from rvsq.login import login_rvsq
    driver = _mock_driver()
    with patch("rvsq.login.navigate_to_rvsq") as mock_nav, \
         patch("rvsq.login._wait_for_form"), \
         patch("rvsq.login._wait_for_post_login", return_value=True):
        mock_nav.return_value = "Rendez-vous"
        login_rvsq(driver, _creds())
    mock_nav.assert_called_once_with(driver)


def test_login_fills_all_fields():
    from rvsq.login import login_rvsq, FIELD_ORDER
    driver = _mock_driver()
    field_element = MagicMock()
    driver.find_element.return_value = field_element
    with patch("rvsq.login.navigate_to_rvsq", return_value="Rendez-vous"), \
         patch("rvsq.login._wait_for_form"), \
         patch("rvsq.login._wait_for_post_login", return_value=True):
        login_rvsq(driver, _creds())
    # Each field must have been cleared and filled
    assert field_element.clear.call_count >= len(FIELD_ORDER)
    assert field_element.send_keys.call_count >= len(FIELD_ORDER)


def test_login_clicks_consent_and_submit():
    from rvsq.login import login_rvsq
    driver = _mock_driver()
    submit = MagicMock()
    consent = MagicMock()
    consent.is_selected.return_value = False
    with patch("rvsq.login.navigate_to_rvsq", return_value="Rendez-vous"), \
         patch("rvsq.login._wait_for_form"), \
         patch("rvsq.login._find_consent_checkbox", return_value=consent), \
         patch("rvsq.login._find_submit_button", return_value=submit), \
         patch("rvsq.login._wait_for_post_login", return_value=True):
        login_rvsq(driver, _creds())
    consent.click.assert_called_once()
    submit.click.assert_called_once()


def test_login_returns_none_on_success():
    from rvsq.login import login_rvsq
    driver = _mock_driver()
    with patch("rvsq.login.navigate_to_rvsq", return_value="Rendez-vous"), \
         patch("rvsq.login._wait_for_form"), \
         patch("rvsq.login._find_consent_checkbox", return_value=MagicMock(is_selected=lambda: False)), \
         patch("rvsq.login._find_submit_button", return_value=MagicMock()), \
         patch("rvsq.login._wait_for_post_login", return_value=True):
        result = login_rvsq(driver, _creds())
    assert result is None


def test_login_returns_error_on_failure():
    from rvsq.login import login_rvsq
    driver = _mock_driver()
    with patch("rvsq.login.navigate_to_rvsq", return_value="Rendez-vous"), \
         patch("rvsq.login._wait_for_form"), \
         patch("rvsq.login._find_consent_checkbox", return_value=MagicMock(is_selected=lambda: False)), \
         patch("rvsq.login._find_submit_button", return_value=MagicMock()), \
         patch("rvsq.login._wait_for_post_login", return_value=False):
        result = login_rvsq(driver, _creds())
    assert isinstance(result, RVSQError)
    assert result.code == "LOGIN_FAILED"


def test_login_returns_cloudflare_error_on_timeout():
    from rvsq.login import login_rvsq
    driver = _mock_driver()
    with patch("rvsq.login.navigate_to_rvsq", return_value="just a moment"):
        result = login_rvsq(driver, _creds())
    assert isinstance(result, RVSQError)
    assert result.code == "CLOUDFLARE"


@pytest.mark.integration
def test_login_integration_reaches_portal():
    """Reaches RVSQ portal without crashing. Does not assert login success."""
    from rvsq.login import login_rvsq
    from selenium_runner import get_driver
    driver = get_driver()
    try:
        result = login_rvsq(driver, _creds())
        assert result is None or isinstance(result, RVSQError)
    finally:
        driver.quit()
