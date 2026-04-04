import time

import undetected_chromedriver as uc

RVSQ_URL = "https://www.rvsq.gouv.qc.ca/prendrerendezvous/Principale.aspx"


def get_driver() -> uc.Chrome:
    """Return a configured undetected Chrome WebDriver.

    undetected-chromedriver patches the browser binary to bypass Cloudflare
    bot-detection. It manages its own chromedriver binary — no webdriver-manager
    needed.
    """
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    return uc.Chrome(options=options, version_main=146)


def navigate_to_rvsq(driver: uc.Chrome, timeout: int = 20) -> str:
    """Navigate to the RVSQ portal and return the page title.

    The portal sits behind a Cloudflare challenge that shows "Just a moment..."
    before redirecting to the real page. We poll until the title changes or the
    timeout elapses. With undetected-chromedriver the bypass should succeed.
    """
    driver.get(RVSQ_URL)
    deadline = time.time() + timeout
    while time.time() < deadline:
        title = driver.title
        if title and "just a moment" not in title.lower():
            return title
        time.sleep(1)
    return driver.title
