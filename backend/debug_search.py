"""
Visual debug script for RVSQ search — step-by-step with pauses.

Usage:
    cd backend
    source .venv/bin/activate
    python debug_search.py
"""
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


def get_visible_driver():
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1280,900")
    return uc.Chrome(options=options, version_main=146)


def step(label):
    print(f"\n▶ {label}")


def main():
    driver = get_visible_driver()
    try:
        driver.get("https://www.rvsq.gouv.qc.ca/prendrerendezvous/Principale.aspx")

        print("=" * 60)
        print("Log in manually, then press ENTER.")
        print("=" * 60)
        input()

        # --- Step 1: find the nav link ---
        step("Looking for 'Prendre rendez-vous' link...")
        links = driver.find_elements(By.XPATH, "//a[contains(text(), 'Prendre rendez-vous dans une clinique')]")
        print(f"  Found {len(links)} matching link(s)")
        for i, l in enumerate(links):
            print(f"  [{i}] text={repr(l.text)}  displayed={l.is_displayed()}  enabled={l.is_enabled()}")

        if not links:
            print("  ❌ Link not found — printing all links:")
            for a in driver.find_elements(By.TAG_NAME, "a"):
                print(f"    {repr(a.text[:50])}  href={a.get_attribute('href') or ''}[:60]")
            input("Press ENTER to quit.")
            return

        input("Press ENTER to click the link...")
        links[0].click()
        print(f"  URL after click: {driver.current_url}")

        # --- Step 2: wait for postal code field ---
        step("Waiting for postal code field (#PostalCode)...")
        try:
            el = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "PostalCode")))
            print(f"  ✓ Found — value={repr(el.get_attribute('value'))}")
        except Exception as e:
            print(f"  ❌ Not found: {e}")
            driver.save_screenshot("/tmp/step2_fail.png")
            print("  Screenshot → /tmp/step2_fail.png")
            input("Press ENTER to quit.")
            return

        input("Press ENTER to fill the form and search...")

        # --- Step 3: fill form ---
        step("Filling postal code...")
        el.clear(); el.send_keys("H2X 1Y4")

        step("Setting radius...")
        Select(driver.find_element(By.ID, "perimeterCombo")).select_by_visible_text("50 km")

        step("Setting date...")
        date_el = driver.find_element(By.ID, "DateRangeStart")
        date_el.clear()
        date_el.send_keys("05-04-2026")
        date_el.send_keys(Keys.ESCAPE)
        print(f"  Date value after entry: {repr(date_el.get_attribute('value'))}")

        step("Setting service type...")
        Select(driver.find_element(By.ID, "consultingReason")).select_by_visible_text("Consultation urgente")

        step("Clicking Rechercher...")
        driver.find_element(By.ID, "searchbutton").click()
        print(f"  URL after search click: {driver.current_url}")

        # --- Step 4: wait for results ---
        step("Waiting for results (a.h-selectClinic or no-results div)...")
        try:
            WebDriverWait(driver, 30).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a.h-selectClinic")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#clinicsWithNoDisponibilitiesContainer")),
                )
            )
            clinics = driver.find_elements(By.CSS_SELECTOR, "a.h-selectClinic")
            no_results = driver.find_elements(By.CSS_SELECTOR, "#clinicsWithNoDisponibilitiesContainer")
            print(f"  ✓ clinic cards: {len(clinics)}  no-results div: {len(no_results)}")
        except Exception as e:
            driver.save_screenshot("/tmp/step4_fail.png")
            print(f"  ❌ Timed out: {e}")
            print(f"  URL: {driver.current_url}")
            print("  Screenshot → /tmp/step4_fail.png")

        input("\nPress ENTER to close.")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
