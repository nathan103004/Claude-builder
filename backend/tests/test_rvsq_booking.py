from unittest.mock import MagicMock, patch
import pytest
from models.rvsq_models import BookingResult, RVSQError
from selenium.common.exceptions import WebDriverException


def test_book_locates_slot_by_id():
    from rvsq.booking import book_slot
    driver = MagicMock()
    slot_el = MagicMock()
    driver.find_element.return_value = slot_el
    with patch("rvsq.booking._wait_for_confirmation", return_value=("RV-001", "Clinique Test", "2026-04-05", "09:30")):
        book_slot(driver, "slot-abc-123")
    driver.find_element.assert_called()


def test_book_returns_confirmation_on_success():
    from rvsq.booking import book_slot
    driver = MagicMock()
    with patch("rvsq.booking._locate_and_click_slot"), \
         patch("rvsq.booking._wait_for_confirmation",
               return_value=("RV-9482", "Clinique Plateau", "2026-04-05", "09:30")):
        result = book_slot(driver, "slot-abc-123")
    assert isinstance(result, BookingResult)
    assert result.confirmation_number == "RV-9482"
    assert result.clinic_name == "Clinique Plateau"


def test_book_returns_slot_taken_error():
    from rvsq.booking import book_slot
    driver = MagicMock()
    with patch("rvsq.booking._locate_and_click_slot"), \
         patch("rvsq.booking._wait_for_confirmation", return_value=None), \
         patch("rvsq.booking._check_slot_taken", return_value=True):
        result = book_slot(driver, "slot-abc-123")
    assert isinstance(result, RVSQError)
    assert result.code == "SLOT_TAKEN"


def test_book_returns_session_expired_error():
    from rvsq.booking import book_slot
    driver = MagicMock()
    with patch("rvsq.booking._locate_and_click_slot"), \
         patch("rvsq.booking._wait_for_confirmation", return_value=None), \
         patch("rvsq.booking._check_slot_taken", return_value=False), \
         patch("rvsq.booking._check_session_expired", return_value=True):
        result = book_slot(driver, "slot-abc-123")
    assert isinstance(result, RVSQError)
    assert result.code == "SESSION_EXPIRED"


def test_book_returns_error_on_webdriver_exception():
    from rvsq.booking import book_slot
    driver = MagicMock()
    with patch("rvsq.booking._locate_and_click_slot", side_effect=WebDriverException("crash")):
        result = book_slot(driver, "slot-abc-123")
    assert isinstance(result, RVSQError)
    assert result.code == "BOOKING_FAILED"


@pytest.mark.integration
def test_book_integration():
    """Manual test — requires a real session and a real available slot."""
    pass
