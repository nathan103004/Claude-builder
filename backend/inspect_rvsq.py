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
        print("ACTION REQUIRED:")
        print("  In the Chrome window, fill in your RAMQ credentials")
        print("  and click 'Continuer' to log in.")
        print("  After you see the post-login page, come back here")
        print("  and press Enter to capture the search form.")
        print("=" * 60)
        input("  >>> Press Enter once you are logged in: ")

        print(f"  Current page: {driver.title}")
        output.append(dump_elements(driver, "post_login_page"))

        # Try to find and click the clinic search nav link
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
                    print()
                    print("=" * 60)
                    print("ACTION REQUIRED:")
                    print("  The search form should now be visible.")
                    print("  Press Enter to also capture the results page after")
                    print("  searching (optional — run a search first).")
                    print("  Or just press Enter now to skip.")
                    print("=" * 60)
                    input("  >>> Run a search then press Enter (or just Enter to skip): ")
                    output.append(dump_elements(driver, "search_results_page"))
                    break
            else:
                print("  No clinic search link found — dumping current page as fallback.")
                output.append(dump_elements(driver, "nav_page"))
        except Exception as e:
            print(f"  Could not navigate to search form: {e}")

    finally:
        driver.quit()

    out_file = "rvsq_elements.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved to {out_file}")
    print("  Share rvsq_elements.json and Claude will fill in all the selectors automatically.")


if __name__ == "__main__":
    main()
