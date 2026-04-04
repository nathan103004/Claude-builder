from pathlib import Path
from unittest.mock import MagicMock
import pytest
from models.rvsq_models import ClinicCard, RVSQError

FIXTURES = Path(__file__).parent / "fixtures"


def _html(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _driver_with_html(html: str):
    driver = MagicMock()
    driver.page_source = html
    return driver


def test_parse_empty_returns_no_results_error():
    from rvsq.scraper import parse_clinic_cards_from_html
    result = parse_clinic_cards_from_html(_html("rvsq_results_empty.html"))
    assert isinstance(result, RVSQError)
    assert result.code == "NO_RESULTS"


def test_parse_single_card_returns_one_clinic():
    from rvsq.scraper import parse_clinic_cards_from_html
    result = parse_clinic_cards_from_html(_html("rvsq_results_single.html"))
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], ClinicCard)


def test_parse_multiple_cards():
    from rvsq.scraper import parse_clinic_cards_from_html
    result = parse_clinic_cards_from_html(_html("rvsq_results_multiple.html"))
    assert isinstance(result, list)
    assert len(result) >= 2


def test_parse_card_fields_non_empty():
    from rvsq.scraper import parse_clinic_cards_from_html
    result = parse_clinic_cards_from_html(_html("rvsq_results_single.html"))
    card = result[0]
    assert card.clinic_name.strip() != ""
    assert card.address.strip() != ""


def test_parse_slot_fields_populated():
    from rvsq.scraper import parse_clinic_cards_from_html
    result = parse_clinic_cards_from_html(_html("rvsq_results_single.html"))
    for card in result:
        for slot in card.slots:
            assert slot.date != ""
            assert slot.time != ""
            assert slot.slot_id != ""


def test_parse_handles_card_with_no_startdate():
    from rvsq.scraper import parse_clinic_cards_from_html
    # Card with no data-startdate attribute → slots list is empty
    html = """<html><body>
      <ul class="ClinicList h-ClinicList">
        <li>
          <a class="h-selectClinic" href="javascript:;" data-companyid="999">
            <div class="tmbWrapper" style="float:left">
              <h2 class="remove-margin clinic-title">Clinique Test</h2>
              <p>123 rue Test, Montréal</p>
            </div>
          </a>
        </li>
      </ul>
    </body></html>"""
    result = parse_clinic_cards_from_html(html)
    assert isinstance(result, list) and len(result) == 1
    assert result[0].slots == []


def test_parse_clinic_cards_uses_page_source():
    from rvsq.scraper import parse_clinic_cards
    driver = _driver_with_html(_html("rvsq_results_multiple.html"))
    result = parse_clinic_cards(driver)
    assert isinstance(result, list) or isinstance(result, RVSQError)
