import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

RVSQ_URL = "https://www.rvsq.gouv.qc.ca/prendrerendezvous/Principale.aspx"


def _get_chromedriver_path() -> str:
    """Return the path to the chromedriver binary.

    webdriver-manager v4 has a bug on macOS where .install() may return a
    non-executable file from the extracted zip (e.g. THIRD_PARTY_NOTICES).
    We resolve the parent directory, locate the actual 'chromedriver' binary,
    and ensure it is executable.
    """
    raw_path = ChromeDriverManager().install()
    driver_dir = os.path.dirname(raw_path)
    candidate = os.path.join(driver_dir, "chromedriver")
    if os.path.isfile(candidate):
        # Ensure the binary is executable (webdriver-manager may not set +x)
        current_mode = os.stat(candidate).st_mode
        os.chmod(candidate, current_mode | 0o111)
        return candidate
    # Fall back to whatever webdriver-manager returned
    return raw_path


def get_driver() -> webdriver.Chrome:
    """Return a configured headless Chrome WebDriver."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    # Reduce Cloudflare bot-detection fingerprint
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    service = Service(_get_chromedriver_path())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


def navigate_to_rvsq(driver: webdriver.Chrome, timeout: int = 20) -> str:
    """Navigate to the RVSQ portal and return the page title.

    The portal sits behind a Cloudflare challenge that shows "Just a moment..."
    before redirecting to the real page. We poll until the title changes or the
    timeout elapses.
    """
    driver.get(RVSQ_URL)
    deadline = time.time() + timeout
    while time.time() < deadline:
        title = driver.title
        if title and "just a moment" not in title.lower():
            return title
        time.sleep(1)
    return driver.title
