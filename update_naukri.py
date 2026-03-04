"""
Naukri Daily Profile Updater
────────────────────────────
Logs into Naukri and makes a tiny rotating change to your resume headline
so your profile appears "recently updated" to recruiters.

Credentials are read from environment variables (set as GitHub Secrets):
    NAUKRI_EMAIL
    NAUKRI_PASSWORD
"""

import os
import time
import random
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("update.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ── Rotating headline suffixes ────────────────────────────────────────────────
# Each day a different suffix is appended/swapped so the profile looks updated.
# Customize your BASE_HEADLINE to match your actual Naukri headline.

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
    """Pick a suffix based on day of year so it rotates daily."""
    day_index = datetime.now().timetuple().tm_yday  # 1–365
    return SUFFIXES[day_index % len(SUFFIXES)]

def update_naukri(email: str, password: str):
    new_headline = f"{BASE_HEADLINE} {get_todays_suffix()}"
    log.info(f"Target headline: {new_headline}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        try:
            # ── Step 1: Go to Naukri login ────────────────────────────────
            log.info("Navigating to Naukri login page…")
            page.goto("https://www.naukri.com/nlogin/login", timeout=30000)
            time.sleep(random.uniform(2, 4))

            # ── Step 2: Fill credentials ──────────────────────────────────
            log.info("Filling login credentials…")
            page.fill("input[placeholder='Enter your active Email ID / Username']", email)
            time.sleep(random.uniform(0.5, 1.5))
            page.fill("input[placeholder='Enter your password']", password)
            time.sleep(random.uniform(0.5, 1.5))

            # Click login button
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle", timeout=20000)
            time.sleep(random.uniform(2, 4))

            log.info(f"Current URL after login: {page.url}")

            # ── Step 3: Go to profile edit page ──────────────────────────
            log.info("Navigating to profile page…")
            page.goto("https://www.naukri.com/mnjuser/profile", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=20000)
            time.sleep(random.uniform(2, 3))

            # ── Step 4: Click "Edit" on Resume Headline section ───────────
            log.info("Looking for Resume Headline edit button…")

            # Try multiple selectors Naukri uses
            headline_edit_selectors = [
                "section[data-section='resumeHeadline'] .edit-button",
                "[data-section='resumeHeadline'] .icon.edit",
                ".resumeHeadline .editIcon",
                "span.edit[title='Edit Resume Headline']",
                # Fallback: find by heading text
                "text=Resume Headline",
            ]

            clicked = False
            for selector in headline_edit_selectors:
                try:
                    el = page.locator(selector).first
                    if el.is_visible(timeout=3000):
                        el.click()
                        clicked = True
                        log.info(f"Clicked edit using selector: {selector}")
                        break
                except Exception:
                    continue

            if not clicked:
                # Last resort: click the pencil icon near "Resume Headline" text
                page.get_by_text("Resume Headline").locator("..").locator(".edit, .pencil, [class*='edit']").first.click()

            time.sleep(random.uniform(1, 2))

            # ── Step 5: Clear and type new headline ───────────────────────
            log.info("Updating headline text…")
            headline_input_selectors = [
                "input[placeholder*='headline' i]",
                "textarea[placeholder*='headline' i]",
                "input[name='resumeHeadline']",
                "textarea[name='resumeHeadline']",
                ".resumeHeadlineArea input",
                ".resumeHeadlineArea textarea",
            ]

            typed = False
            for selector in headline_input_selectors:
                try:
                    el = page.locator(selector).first
                    if el.is_visible(timeout=3000):
                        el.triple_click()  # select all
                        el.type(new_headline, delay=random.randint(40, 90))
                        typed = True
                        log.info(f"Typed headline using selector: {selector}")
                        break
                except Exception:
                    continue

            if not typed:
                log.error("Could not find headline input field. Taking screenshot for debug.")
                page.screenshot(path="debug_screenshot.png")
                raise RuntimeError("Headline input not found")

            time.sleep(random.uniform(1, 2))

            # ── Step 6: Save ──────────────────────────────────────────────
            log.info("Saving changes…")
            save_selectors = [
                "button:has-text('Save')",
                "button[type='submit']",
                ".saveBtn",
                "input[value='Save']",
            ]
            for selector in save_selectors:
                try:
                    el = page.locator(selector).first
                    if el.is_visible(timeout=3000):
                        el.click()
                        log.info(f"Saved using selector: {selector}")
                        break
                except Exception:
                    continue

            time.sleep(random.uniform(2, 3))

            # ── Step 7: Confirm success ───────────────────────────────────
            log.info("✅ Profile updated successfully!")
            log.info(f"New headline set to: {new_headline}")
            page.screenshot(path="success_screenshot.png")

        except PWTimeout as e:
            log.error(f"Timeout error: {e}")
            page.screenshot(path="error_screenshot.png")
            raise
        except Exception as e:
            log.error(f"Unexpected error: {e}")
            page.screenshot(path="error_screenshot.png")
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    email = os.environ.get("NAUKRI_EMAIL")
    password = os.environ.get("NAUKRI_PASSWORD")

    if not email or not password:
        raise ValueError(
            "Missing credentials! Set NAUKRI_EMAIL and NAUKRI_PASSWORD "
            "as environment variables or GitHub Secrets."
        )

    update_naukri(email, password)
