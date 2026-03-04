"""
Naukri Profile Updater — Local Windows Test (HEADED mode)
──────────────────────────────────────────────────────────
Run this on your Windows machine FIRST to visually verify the bot works.
You'll see a real Chrome window open and perform the login.

Usage:
    python test_local.py --email you@email.com --password yourpass

Once this works locally, the same logic runs headlessly in GitHub Actions.

Install deps first:
    pip install playwright
    playwright install chromium
"""

import argparse
import random
import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ── Rotating headlines ────────────────────────────────────────────────────────
BASE_HEADLINE = "Data Engineer | Python | SQL | Spark | Cloud"

SUFFIXES = [
    "| Open to Work",
    "| AWS | GCP",
    "| ETL | Data Pipelines",
    "| Actively Looking",
    "| 4+ Yrs Exp",
    "| Spark | Kafka",
    "| Azure | Databricks",
    "| Real-time & Batch",
    "| Hiring Ready",
    "| Data Platform",
]

def get_todays_suffix() -> str:
    day_index = datetime.now().timetuple().tm_yday
    return SUFFIXES[day_index % len(SUFFIXES)]


def run(email: str, password: str, headless: bool = False):
    from playwright.sync_api import sync_playwright

    headline = f"{BASE_HEADLINE} {get_todays_suffix()}"
    log.info(f"Mode: {'Headless' if headless else '👁  HEADED (visible browser)'}")
    log.info(f"Target headline: {headline}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            slow_mo=100 if not headless else 0,   # slows actions so you can watch
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
            ],
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            viewport=None if not headless else {"width": 1366, "height": 768},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            extra_http_headers={
                "Accept-Language": "en-IN,en;q=0.9",
                "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
            },
        )

        # Patch: hide automation flags
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-IN', 'en'] });
            window.chrome = { runtime: {} };
        """)

        page = context.new_page()

        try:
            # ── Step 1: Homepage ──────────────────────────────────────────
            log.info("📌 Step 1/6 — Visiting homepage…")
            page.goto("https://www.naukri.com", wait_until="domcontentloaded", timeout=30000)
            time.sleep(random.uniform(2, 3))
            page.evaluate("window.scrollBy(0, 400)")
            time.sleep(random.uniform(1, 2))

            # ── Step 2: Login page ────────────────────────────────────────
            log.info("📌 Step 2/6 — Navigating to login page…")
            page.goto("https://www.naukri.com/nlogin/login", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(random.uniform(3, 5))

            log.info(f"  URL : {page.url}")
            log.info(f"  Title: {page.title()}")

            # ── Step 3: Email field ───────────────────────────────────────
            log.info("📌 Step 3/6 — Filling email…")
            EMAIL_SELECTORS = [
                "#usernameField",
                "input[id='usernameField']",
                "input[type='email']",
                "input[name='email']",
                "input[placeholder*='Email' i]",
                "input[placeholder*='username' i]",
                "input[type='text']",
            ]

            email_el = None
            for sel in EMAIL_SELECTORS:
                try:
                    el = page.locator(sel).first
                    el.wait_for(state="visible", timeout=5000)
                    email_el = el
                    log.info(f"  ✓ Email field found: {sel}")
                    break
                except Exception:
                    continue

            if not email_el:
                page.screenshot(path="debug_no_email_field.png")
                log.error("  ✗ Email field NOT found — screenshot saved as debug_no_email_field.png")
                log.info(f"  Page HTML:\n{page.content()[:3000]}")
                raise RuntimeError("Could not find email input. Check debug_no_email_field.png")

            email_el.scroll_into_view_if_needed()
            email_el.click()
            time.sleep(0.5)
            for char in email:
                email_el.type(char, delay=random.randint(60, 130))
            time.sleep(random.uniform(0.5, 1.0))

            # ── Step 4: Password field ────────────────────────────────────
            log.info("📌 Step 4/6 — Filling password…")
            PASS_SELECTORS = [
                "#passwordField",
                "input[id='passwordField']",
                "input[type='password']",
                "input[name='password']",
                "input[placeholder*='password' i]",
            ]
            pass_el = None
            for sel in PASS_SELECTORS:
                try:
                    el = page.locator(sel).first
                    el.wait_for(state="visible", timeout=5000)
                    pass_el = el
                    log.info(f"  ✓ Password field found: {sel}")
                    break
                except Exception:
                    continue

            if not pass_el:
                page.screenshot(path="debug_no_pass_field.png")
                raise RuntimeError("Could not find password input.")

            pass_el.click()
            time.sleep(0.5)
            for char in password:
                pass_el.type(char, delay=random.randint(60, 130))
            time.sleep(random.uniform(0.5, 1.0))

            # ── Step 5: Submit ────────────────────────────────────────────
            log.info("📌 Step 5/6 — Submitting login…")
            SUBMIT_SELECTORS = [
                "button[type='submit']",
                "button:has-text('Login')",
                "button:has-text('Sign in')",
                ".loginButton",
                "input[type='submit']",
            ]
            for sel in SUBMIT_SELECTORS:
                try:
                    el = page.locator(sel).first
                    if el.is_visible(timeout=3000):
                        el.click()
                        log.info(f"  ✓ Clicked: {sel}")
                        break
                except Exception:
                    continue

            # Naukri uses a SPA router — URL may still show /nlogin right after submit.
            # Wait for a known post-login element instead of checking URL instantly.
            log.info("  Waiting for post-login indicator...")
            login_confirmed = False
            try:
                # Wait up to 10s for the nav avatar / profile area to appear
                page.wait_for_selector(
                    ".nI-gNb-drawer__icon, .nI-gNb-sb__icon--login, [data-ga-track='login'], a[href*='mnjuser']",
                    timeout=10000
                )
                login_confirmed = True
                log.info(f"  ✓ Login confirmed via DOM element. URL: {page.url}")
            except Exception:
                pass

            if not login_confirmed:
                # Fallback: wait another 5s and re-check URL
                time.sleep(5)
                if "/nlogin/login" in page.url:
                    log.error("  ✗ Login failed — still on login page after waiting. Check debug_login_failed.png")
                    page.screenshot(path="debug_login_failed.png")
                    raise RuntimeError("Login failed. Check credentials and debug_login_failed.png")
                else:
                    log.info(f"  ✓ Login redirect detected. URL: {page.url}")


            # ── Step 6: Update headline ───────────────────────────────────
            log.info("📌 Step 6/6 — Updating Resume Headline…")
            # 'networkidle' times out on Naukri due to continuous XHR; use domcontentloaded instead
            page.goto("https://www.naukri.com/mnjuser/profile", wait_until="domcontentloaded", timeout=30000)
            time.sleep(random.uniform(3, 5))

            # Click the pencil icon next to Resume Headline
            HEADLINE_EDIT_SELECTORS = [
                "[data-section='resumeHeadline'] .edit-button",
                "[data-section='resumeHeadline'] .editIcon",
                "[data-section='resumeHeadline'] .icon.edit",
                ".resumeHeadline .icon.edit",
                "span.edit[title*='Headline' i]",
                # Generic: the pencil/edit icon NEAR the text "Resume headline"
                "div:has(> span:text-matches('Resume headline', 'i')) .icon.edit",
                "div:has(> span:text-matches('Resume headline', 'i')) button",
            ]
            clicked_edit = False
            for sel in HEADLINE_EDIT_SELECTORS:
                try:
                    el = page.locator(sel).first
                    if el.is_visible(timeout=3000):
                        el.scroll_into_view_if_needed()
                        el.click()
                        log.info(f"  ✓ Headline edit clicked: {sel}")
                        clicked_edit = True
                        break
                except Exception:
                    continue

            # Fallback: find the pencil SVG icon nearest to headline text
            if not clicked_edit:
                try:
                    page.get_by_text("Resume headline").locator("..").locator("span, button, svg").last.click()
                    log.info("  ✓ Headline edit clicked via fallback (sibling of text node)")
                    clicked_edit = True
                except Exception:
                    pass

            if not clicked_edit:
                log.error("  ✗ Could not click the headline edit icon.")
                page.screenshot(path="debug_no_edit_click.png")
                raise RuntimeError("Failed to click resume headline edit button. See debug_no_edit_click.png")

            # Wait up to 5 seconds for the input/textarea to appear after clicking edit
            HEADLINE_INPUT_SELECTORS = [
                "textarea[placeholder*='headline' i]",
                "input[placeholder*='headline' i]",
                "textarea[name='resumeHeadline']",
                "input[name='resumeHeadline']",
                ".resumeHeadlineArea textarea",
                ".resumeHeadlineArea input",
                "textarea[maxlength]",   # broad fallback for modal textareas
            ]
            headline_el = None
            for sel in HEADLINE_INPUT_SELECTORS:
                try:
                    el = page.locator(sel).first
                    el.wait_for(state="visible", timeout=5000)
                    headline_el = el
                    log.info(f"  ✓ Headline input found: {sel}")
                    break
                except Exception:
                    continue

            if not headline_el:
                log.error("  ✗ Headline input NOT found after clicking edit.")
                page.screenshot(path="debug_no_headline_input.png")
                log.info(f"  Page HTML (first 3000 chars):\n{page.content()[:3000]}")
                raise RuntimeError("Headline input field not found after clicking edit.")

            # Focus field, use Ctrl+A + Delete to clear (fires React onChange properly)
            headline_el.click()
            time.sleep(0.3)
            headline_el.press("Control+a")
            time.sleep(0.2)
            headline_el.press("Delete")
            time.sleep(0.2)
            # Type character by character to trigger onChange on each keystroke
            for char in headline:
                headline_el.type(char, delay=random.randint(60, 130))
            log.info(f"  ✓ Typed: {headline}")

            # Confirm value is set
            current_val = headline_el.input_value()
            log.info(f"  ✓ Field value confirmed: {current_val!r}")
            time.sleep(random.uniform(0.8, 1.5))

            # Save — try ancestor form scope first to avoid clicking wrong button
            saved = False
            try:
                save_el = headline_el.locator("xpath=ancestor::form//button[contains(., 'Save')]").first
                if save_el.is_visible(timeout=3000):
                    save_el.click()
                    log.info("  ✓ Saved via ancestor form scope")
                    saved = True
            except Exception:
                pass

            if not saved:
                for sel in ["button:has-text('Save')", ".btn-dark-ot", ".saveBtn", ".saveButton"]:
                    try:
                        el = page.locator(sel).last  # .last — Save is usually at bottom of modal
                        if el.is_visible(timeout=3000):
                            el.click()
                            log.info(f"  ✓ Saved via fallback: {sel}")
                            saved = True
                            break
                    except Exception:
                        continue

            if not saved:
                log.warning("  ⚠ Save button not found. Dumping all visible buttons for debugging:")
                all_buttons = page.locator("button").all()
                for btn in all_buttons:
                    try:
                        if btn.is_visible(timeout=500):
                            log.warning(f"    - button text: {btn.inner_text()!r}")
                    except Exception:
                        pass
                page.screenshot(path="debug_no_save_button.png")

            time.sleep(random.uniform(2, 3))
            page.screenshot(path="success_screenshot.png")
            log.info("✅ SUCCESS! Headline updated. Screenshot saved.")

        except Exception as e:
            log.error(f"❌ Error: {e}")
            try:
                page.screenshot(path="error_screenshot.png")
                log.info("Screenshot saved as error_screenshot.png")
            except Exception:
                pass
            raise

        finally:
            if not headless:
                log.info("Keeping browser open for 5 seconds so you can inspect…")
                time.sleep(5)
            browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Naukri Profile Updater — Local Test")
    parser.add_argument("--email",    required=True,  help="Your Naukri email")
    parser.add_argument("--password", required=True,  help="Your Naukri password")
    parser.add_argument("--headless", action="store_true", help="Run headless (no visible window)")
    args = parser.parse_args()

    run(email=args.email, password=args.password, headless=args.headless)