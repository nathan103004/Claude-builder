from unittest.mock import MagicMock, patch
import pytest
from models.rvsq_models import SearchParams, RVSQError, SERVICE_TYPE_MAP


def _params(service_type="consultation_urgente"):
    return SearchParams(
        code_postal="H2X 1Y4",
        service_type=service_type,
        date_debut="2026-04-05",
    )


def test_service_type_map_covers_all_options():
    keys = ["consultation_urgente", "consultation_semi_urgente", "suivi", "suivi_pediatrique", "suivi_grossesse"]
    for k in keys:
        assert k in SERVICE_TYPE_MAP
        assert isinstance(SERVICE_TYPE_MAP[k], str)
        assert len(SERVICE_TYPE_MAP[k]) > 0


def test_search_returns_error_for_invalid_service_type():
    from rvsq.search import search_clinics
    driver = MagicMock()
    result = search_clinics(driver, SearchParams(
        code_postal="H2X 1Y4", service_type="invalid_type", date_debut="2026-04-05"
    ))
    assert isinstance(result, RVSQError)
    assert result.code == "INVALID_SERVICE_TYPE"


def test_search_fills_postal_code():
    from rvsq.search import search_clinics
    driver = MagicMock()
    field = MagicMock()
    driver.find_element.return_value = field
    with patch("rvsq.search._navigate_to_search_form"), \
         patch("rvsq.search._set_service_type"), \
         patch("rvsq.search._set_moments"), \
         patch("rvsq.search._click_search"), \
         patch("rvsq.search._wait_for_results"), \
         patch("rvsq.search.parse_clinic_cards", return_value=[]):
        search_clinics(driver, _params())
    # Postal code field must have been filled
    calls = [str(c) for c in field.send_keys.call_args_list]
    assert any("H2X 1Y4" in c for c in calls)


def test_search_returns_error_on_session_expired():
    from rvsq.search import search_clinics
    from selenium.common.exceptions import WebDriverException
    driver = MagicMock()
    driver.find_element.side_effect = WebDriverException("session expired")
    with patch("rvsq.search._navigate_to_search_form", side_effect=WebDriverException("session expired")):
        result = search_clinics(driver, _params())
    assert isinstance(result, RVSQError)
    assert result.code == "SESSION_EXPIRED"


def test_search_checks_all_moment_checkboxes():
    from rvsq.search import search_clinics, MOMENTS
    driver = MagicMock()
    checkbox = MagicMock()
    checkbox.is_selected.return_value = False
    driver.find_element.return_value = checkbox
    with patch("rvsq.search._navigate_to_search_form"), \
         patch("rvsq.search._fill_postal_code"), \
         patch("rvsq.search._set_radius"), \
         patch("rvsq.search._set_date"), \
         patch("rvsq.search._set_service_type"), \
         patch("rvsq.search._click_search"), \
         patch("rvsq.search._wait_for_results"), \
         patch("rvsq.search.parse_clinic_cards", return_value=[]):
        search_clinics(driver, _params())
    # One click per unchecked moment checkbox
    assert checkbox.click.call_count >= len(MOMENTS)


@pytest.mark.integration
def test_search_integration():
    """Reaches search form without crashing. Requires a live authenticated session."""
    pass  # Implement manually with a real session during QA
