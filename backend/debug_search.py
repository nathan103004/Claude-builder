"""
Visual debug script for RVSQ search — auto-login + step-by-step search.

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

from models.rvsq_models import RAMQCredentials, SearchParams, RVSQError
from rvsq.login import login_rvsq
from rvsq.search import search_clinics


def get_visible_driver():
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1280,900")
    return uc.Chrome(options=options, version_main=146)


def prompt_credentials() -> RAMQCredentials:
    print("\n--- RAMQ credentials ---")
    prenom   = input("Prénom            : ").strip()
    nom      = input("Nom               : ").strip()
    ramq     = input("Numéro RAMQ       : ").strip()
    seq      = input("Numéro séquentiel : ").strip()
    jour     = input("Jour naissance    : ").strip()
    mois     = input("Mois naissance    : ").strip()
    annee    = input("Année naissance   : ").strip()
    return RAMQCredentials(
        prenom=prenom, nom=nom,
        numero_assurance_maladie=ramq,
        numero_sequentiel=seq,
        date_naissance_jour=jour,
        date_naissance_mois=mois,
        date_naissance_annee=annee,
    )


def main():
    credentials = prompt_credentials()
    postal_code = input("Code postal [H2X 1Y4]: ").strip() or "H2X 1Y4"

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
