"""
Visual debug script for RVSQ search — auto-login + step-by-step search.

Usage:
    cd backend
    source .venv/bin/activate
    python debug_search.py
"""
import os
import time
import undetected_chromedriver as uc
from dotenv import load_dotenv

from models.rvsq_models import RAMQCredentials, SearchParams, RVSQError
from rvsq.login import login_rvsq
from rvsq.search import search_clinics

load_dotenv()


def get_visible_driver():
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1280,900")
    return uc.Chrome(options=options, version_main=146)


def load_credentials() -> tuple[RAMQCredentials, str]:
    credentials = RAMQCredentials(
        prenom=os.getenv("DEBUG_PRENOM", ""),
        nom=os.getenv("DEBUG_NOM", ""),
        numero_assurance_maladie=os.getenv("DEBUG_RAMQ", ""),
        numero_sequentiel=os.getenv("DEBUG_SEQ", ""),
        date_naissance_jour=os.getenv("DEBUG_JOUR", ""),
        date_naissance_mois=os.getenv("DEBUG_MOIS", ""),
        date_naissance_annee=os.getenv("DEBUG_ANNEE", ""),
    )
    postal_code = os.getenv("DEBUG_POSTAL", "H2X 1Y4")
    return credentials, postal_code


def main():
    credentials, postal_code = load_credentials()
    print(f"Using credentials: {credentials.prenom} {credentials.nom} / RAMQ {credentials.numero_assurance_maladie}")
    print(f"Postal code: {postal_code}")

    driver = get_visible_driver()
    try:
        # --- Login ---
        print("\n▶ Logging in automatically...")
        error = login_rvsq(driver, credentials)
        if error:
            print(f"  ❌ Login failed: {error.code} — {error.message}")
            input("Press ENTER to close.")
            return
        print(f"  ✓ Logged in. URL: {driver.current_url}")

        params = SearchParams(
            code_postal=postal_code,
            service_type="consultation_urgente",
            date_debut=time.strftime("%Y-%m-%d"),
            rayon_km=50,
            moments=["avant-midi", "apres-midi", "soir"],
        )

        # --- Search loop ---
        attempt = 0
        while True:
            attempt += 1
            print(f"\n--- Attempt {attempt} ---")
            result = search_clinics(driver, params)

            if isinstance(result, list) and len(result) > 0:
                print(f"✓ Found {len(result)} clinic(s)!")
                for c in result[:5]:
                    print(f"  {c.clinic_name}  ({len(c.slots)} slot(s))")
                    for s in c.slots[:3]:
                        print(f"    {s.date} {s.time}  slot_id={s.slot_id}")
                break

            elif isinstance(result, list):
                print("  No clinics this attempt — retrying in 5s...")

            elif isinstance(result, RVSQError):
                screenshot = f"/tmp/rvsq_attempt{attempt}.png"
                driver.save_screenshot(screenshot)
                print(f"  ERROR {result.code}: {result.message}")
                print(f"  URL: {driver.current_url}  screenshot → {screenshot}")
                retry = input("  Press ENTER to retry, or 'q' to quit: ").strip()
                if retry.lower() == "q":
                    break

            time.sleep(5)

        input("\nPress ENTER to close the browser...")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
