"""
Visual debug script for RVSQ search.
Opens a real browser window so you can watch exactly where the search fails.

Usage:
    cd backend
    source .venv/bin/activate
    python debug_search.py
"""
import sys
import time
import undetected_chromedriver as uc
from models.rvsq_models import SearchParams
from rvsq.search import search_clinics


def get_visible_driver():
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1280,900")
    return uc.Chrome(options=options, version_main=146)


def main():
    driver = get_visible_driver()
    try:
        driver.get("https://www.rvsq.gouv.qc.ca/prendrerendezvous/Principale.aspx")

        print("=" * 60)
        print("1. Log in manually in the browser window.")
        print("2. Wait until you reach the post-login welcome page.")
        print("=" * 60)
        input("Press ENTER here when you are logged in...")

        postal_code = input("Postal code to search [H2X 1Y4]: ").strip() or "H2X 1Y4"

        params = SearchParams(
            code_postal=postal_code,
            service_type="consultation_urgente",
            date_debut="2026-04-05",
            rayon_km=50,
            moments=["avant-midi", "apres-midi", "soir"],
        )

        print(f"\nCurrent URL : {driver.current_url}")
        print(f"Page title  : {driver.title}")

        from selenium.webdriver.common.by import By
        links = driver.find_elements(By.TAG_NAME, "a")
        print(f"\nAll <a> hrefs on this page ({len(links)} total):")
        for a in links:
            href = a.get_attribute("href") or ""
            text = a.text.strip()
            if href or text:
                print(f"  [{text[:40]}]  href={href[:80]}")

        input("\nCheck the list above, then press ENTER to run search_clinics()...")

        result = search_clinics(driver, params)

        print("\n--- RESULT ---")
        if isinstance(result, list):
            print(f"Found {len(result)} clinic(s).")
            for c in result[:5]:
                print(f"  {c.clinic_name}  ({len(c.slots)} slot(s))")
                for s in c.slots[:2]:
                    print(f"    {s.date} {s.time}  slot_id={s.slot_id}")
        else:
            print(f"ERROR {result.code}: {result.message}")

        input("\nPress ENTER to close the browser...")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
