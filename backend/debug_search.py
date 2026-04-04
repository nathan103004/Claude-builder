"""
Visual debug script for RVSQ search.
Opens a real browser window so you can watch exactly where the search fails.

Usage:
    cd backend
    source .venv/bin/activate
    python debug_search.py
"""
import time
import undetected_chromedriver as uc
from models.rvsq_models import SearchParams, RVSQError
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

        attempt = 0
        while True:
            attempt += 1
            print(f"\n--- Attempt {attempt} ---")
            print(f"URL: {driver.current_url}")

            result = search_clinics(driver, params)

            if isinstance(result, list) and len(result) > 0:
                print(f"Found {len(result)} clinic(s)!")
                for c in result[:5]:
                    print(f"  {c.clinic_name}  ({len(c.slots)} slot(s))")
                    for s in c.slots[:2]:
                        print(f"    {s.date} {s.time}  slot_id={s.slot_id}")
                break

            elif isinstance(result, list) and len(result) == 0:
                print("No clinics found this attempt. Retrying in 5s...")

            elif isinstance(result, RVSQError):
                # Take a screenshot so we can see the page state
                screenshot_path = f"/tmp/rvsq_debug_attempt{attempt}.png"
                driver.save_screenshot(screenshot_path)
                print(f"ERROR {result.code}: {result.message}")
                print(f"Screenshot saved → {screenshot_path}")
                print(f"Current URL: {driver.current_url}")
                print(f"Page title : {driver.title}")
                retry = input("Press ENTER to retry, or type 'q' to quit: ").strip()
                if retry.lower() == "q":
                    break

            time.sleep(5)

        input("\nPress ENTER to close the browser...")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
