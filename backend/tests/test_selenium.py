import pytest
from selenium_runner import get_driver, navigate_to_rvsq


@pytest.mark.integration
def test_driver_launches_and_navigates():
    driver = get_driver()
    try:
        title = navigate_to_rvsq(driver)
        # With undetected-chromedriver the Cloudflare challenge should be bypassed.
        # The real RVSQ portal title contains one of these substrings.
        assert (
            "Rendez-vous" in title
            or "santé" in title.lower()
            or "québec" in title.lower()
        ), f"Unexpected page title: {title!r}"
    finally:
        driver.quit()
