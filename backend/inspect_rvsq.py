"""
One-time script: open RVSQ portal with Selenium and dump all
form elements + their IDs/names/CSS selectors so we can fill
in the placeholder constants in rvsq/login.py, search.py, booking.py.

Run:
    cd backend
    source .venv/bin/activate
    python inspect_rvsq.py
"""
import json
import os
import time

# Fix macOS SSL cert verification for undetected_chromedriver's urllib calls
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
except ImportError:
    pass  # certifi not installed — will try without

import undetected_chromedriver as uc

RVSQ_URL = "https://www.rvsq.gouv.qc.ca/prendrerendezvous/Principale.aspx"


def get_driver():
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1280,900")
    driver = uc.Chrome(options=options, headless=False, version_main=146)
    return driver


def navigate_to_rvsq(driver, timeout=30):
    driver.get(RVSQ_URL)
    deadline = time.time() + timeout
    while time.time() < deadline:
        title = driver.title
        if "just a moment" not in title.lower():
            return title
        time.sleep(2)
    return driver.title


def dump_elements(driver, label: str) -> dict:
    script = """
    const results = {};

    // All inputs
    results.inputs = Array.from(document.querySelectorAll('input')).map(el => ({
        tag: 'input', id: el.id, name: el.name, type: el.type,
        placeholder: el.placeholder, value: el.value.slice(0, 40),
        classes: el.className
    }));

    // All selects
    results.selects = Array.from(document.querySelectorAll('select')).map(el => ({
        tag: 'select', id: el.id, name: el.name, classes: el.className,
        options: Array.from(el.options).map(o => o.text).slice(0, 10)
    }));

    // All buttons / submit inputs
    results.buttons = Array.from(document.querySelectorAll('button, input[type=submit], input[type=button]')).map(el => ({
        tag: el.tagName.toLowerCase(), id: el.id, name: el.name,
        text: (el.innerText || el.value || '').slice(0, 60),
        classes: el.className
    }));

    // All checkboxes
    results.checkboxes = Array.from(document.querySelectorAll('input[type=checkbox]')).map(el => ({
        tag: 'checkbox', id: el.id, name: el.name, classes: el.className
    }));

    // Divs/spans that look like error messages
    results.alerts = Array.from(document.querySelectorAll(
        '[class*=error],[class*=alert],[class*=message],[class*=warning],[role=alert]'
    )).map(el => ({
        tag: el.tagName.toLowerCase(), id: el.id, classes: el.className,
        text: (el.innerText || '').slice(0, 80)
    }));

    // Clinic cards (search results page)
    results.clinic_cards = Array.from(document.querySelectorAll('a.h-selectClinic, [class*=selectClinic], [class*=clinic]')).slice(0, 5).map(el => ({
        tag: el.tagName.toLowerCase(), id: el.id, classes: el.className,
        data: Object.fromEntries(Array.from(el.attributes).filter(a => a.name.startsWith('data-')).map(a => [a.name, a.value])),
        text: (el.innerText || '').slice(0, 100)
    }));

    // Slot/time buttons (slot calendar page)
    results.slot_buttons = Array.from(document.querySelectorAll(
        '[class*=slot],[class*=Slot],[class*=heure],[class*=time],[class*=disponible],[class*=available]'
    )).slice(0, 10).map(el => ({
        tag: el.tagName.toLowerCase(), id: el.id, classes: el.className,
        data: Object.fromEntries(Array.from(el.attributes).filter(a => a.name.startsWith('data-')).map(a => [a.name, a.value])),
        text: (el.innerText || '').slice(0, 60)
    }));

    // Confirmation number (booking confirmation page)
    results.confirmation_elements = Array.from(document.querySelectorAll(
        '[class*=confirm],[class*=Confirm],[class*=number],[class*=numero],[class*=reference],[class*=Reference]'
    )).slice(0, 10).map(el => ({
        tag: el.tagName.toLowerCase(), id: el.id, classes: el.className,
        text: (el.innerText || '').slice(0, 100)
    }));

    // ALL anchors and clickable elements (for clinic card discovery)
    results.all_anchors = Array.from(document.querySelectorAll('a[class]')).slice(0, 20).map(el => ({
        tag: 'a', id: el.id, classes: el.className, href: (el.href||'').slice(0,80),
        data: Object.fromEntries(Array.from(el.attributes).filter(a => a.name.startsWith('data-')).map(a => [a.name, a.value])),
        text: (el.innerText || '').slice(0, 60)
    }));

    return results;
    """
    data = driver.execute_script(script)
    return {"page": label, "url": driver.current_url, "title": driver.title, **data}


def main():
    driver = get_driver()
    output = []

    try:
        print("Navigating to RVSQ login page...")
        title = navigate_to_rvsq(driver)
        print(f"  Title: {title}")

        if "just a moment" in title.lower():
            print("  ⚠ Cloudflare challenge detected. Waiting 20s for it to pass...")
            time.sleep(20)
            print(f"  Title after wait: {driver.title}")

        print("Dumping login form elements...")
        output.append(dump_elements(driver, "login_page"))

        print()
        print("=" * 60)
        print("STEP 1 — LOG IN:")
        print("  Fill in your RAMQ credentials and click Continuer.")
        print("  Come back here once you see the post-login page.")
        print("=" * 60)
        input("  >>> Press Enter once logged in: ")

        print(f"  Current page: {driver.title}")
        output.append(dump_elements(driver, "post_login_page"))

        # Navigate to clinic search
        print("Looking for clinic search navigation...")
        try:
            links = driver.find_elements("css selector", "a")
            for link in links:
                text = (link.text or "").lower()
                if "clinique" in text or "proximité" in text or "rendez-vous" in text:
                    print(f"  Clicking: {link.text.strip()!r}")
                    link.click()
                    time.sleep(3)
                    output.append(dump_elements(driver, "clinic_search_page"))
                    break
            else:
                print("  No clinic search link found — dumping current page as fallback.")
                output.append(dump_elements(driver, "clinic_search_page"))
        except Exception as e:
            print(f"  Could not navigate to search form: {e}")

        print()
        print("=" * 60)
        print("STEP 2 — SEARCH WITH A POSTAL CODE THAT HAS RESULTS:")
        print("  Use: H2X 1Y6 or H3H 1V4 (central Montreal — usually has slots)")
        print("  Fill postal code, set radius to 50 km, pick any service type.")
        print("  Click Rechercher and WAIT for clinic cards to appear.")
        print("  Then come back here and press Enter.")
        print("=" * 60)
        input("  >>> Run search, wait for results, then press Enter: ")

        output.append(dump_elements(driver, "search_results_page"))

        print()
        print("=" * 60)
        print("STEP 3 — CLICK A CLINIC CARD:")
        print("  In the browser, click on any clinic card that shows availability.")
        print("  You should land on a slot calendar / time picker page.")
        print("  Come back here and press Enter.")
        print("=" * 60)
        input("  >>> Click a clinic card, then press Enter: ")

        output.append(dump_elements(driver, "slot_calendar_page"))

        print()
        print("=" * 60)
        print("STEP 4 (OPTIONAL) — SELECT A SLOT AND CONFIRM:")
        print("  Click a time slot then click Confirmer le rendez-vous.")
        print("  This captures the confirmation number element.")
        print("  SKIP this if you don't want to actually book an appointment.")
        print("=" * 60)
        choice = input("  >>> Press Enter to capture confirmation page, or type 'skip' to skip: ").strip().lower()

        if choice != "skip":
            output.append(dump_elements(driver, "confirmation_page"))
        else:
            print("  Skipping confirmation page capture.")

    finally:
        driver.quit()

    out_file = "rvsq_elements.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved to {out_file}")
    print("  Claude will now read this file and fill in all selectors automatically.")


if __name__ == "__main__":
    main()
