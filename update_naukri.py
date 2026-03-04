"""
Naukri Daily Profile Updater
────────────────────────────
Logs into Naukri and makes a tiny rotating change to your resume headline
so your profile appears "recently updated" to recruiters.

credentials get from environment variables: NAUKRI_EMAIL, NAUKRI_PASSWORD
"""

import os
import sys
import time
import random
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from playwright_stealth import stealth_sync

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("update.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

BASE_HEADLINE = "Data Engineer | Python | SQL | Spark | Cloud"
SUFFIXES = ["•", "▪", "·", "‣", "◦"]
SESSION_FILE = "naukri_session.json"

# List of realistic user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15"
]

def get_todays_suffix() -> str:
    """Pick a suffix based on day of year."""
    day_index = datetime.now().timetuple().tm_yday
    return SUFFIXES[day_index % len(SUFFIXES)]

def human_type(page, selector, text):
    """Simulate human typing with random delays."""
    for char in text:
        page.type(selector, char, delay=random.randint(80, 200))

def simulate_reading(page):
    """Scroll down randomly to simulate human reading."""
    log.info("Simulating human reading (scrolling).")
    for _ in range(random.randint(1, 4)):
        page.mouse.wheel(delta_x=0, delta_y=random.randint(100, 500))
        time.sleep(random.uniform(0.5, 2))
    page.mouse.wheel(delta_x=0, delta_y=-random.randint(200, 800))
    time.sleep(random.uniform(1, 3))

def update_naukri(email: str, password: str):
    new_headline = f"{BASE_HEADLINE} {get_todays_suffix()}"
    log.info(f"Target headline: {new_headline}")

    viewport_width = random.choice([1366, 1920])
    viewport_height = random.choice([768, 1080])
    user_agent = random.choice(USER_AGENTS)

    log.info(f"Using User-Agent: {user_agent}")
    log.info(f"Using Viewport: {viewport_width}x{viewport_height}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--use-gl=desktop",
                "--no-default-browser-check",
            ],
        )

        context_args = {
            "user_agent": user_agent,
            "viewport": {"width": viewport_width, "height": viewport_height},
            "extra_http_headers": {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.google.com/",
            },
            "device_scale_factor": 1,
            "is_mobile": False,
            "has_touch": False,
        }

        # Check for existing session
        if os.path.exists(SESSION_FILE):
            log.info("Found existing session file, loading state...")
            context_args["storage_state"] = SESSION_FILE
        
        context = browser.new_context(**context_args)
        page = context.new_page()
        stealth_sync(page)
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            # Step 1: Visit homepage to build trust and check session
            log.info("Visiting homepage...")
            page.goto("https://www.naukri.com/", timeout=45000, wait_until="domcontentloaded")
            time.sleep(random.uniform(3, 6))

            # Check if logged in already (look for 'My Naukri' or profile avatar)
            is_logged_in = page.locator("a:has-text('My Naukri'), img[alt*='profile'], .nI-gNb-drawer__icon").count() > 0

            if not is_logged_in:
                log.info("Not logged in. Proceeding to login page.")
                page.goto("https://www.naukri.com/nlogin/login", timeout=30000)
                time.sleep(random.uniform(4, 7))

                simulate_reading(page)

                log.info("Filling login credentials...")
                email_selector = "input[id='usernameField'], input[placeholder*='Email ID'], input[type='text']"
                box = page.locator(email_selector).first.bounding_box()
                if box:
                    page.mouse.move(box["x"] + box["width"]/2, box["y"] + box["height"]/2, steps=10)
                page.locator(email_selector).first.click()
                human_type(page, email_selector, email)

                time.sleep(random.uniform(1.5, 3.5))

                pass_selector = "input[id='passwordField'], input[type='password']"
                box = page.locator(pass_selector).first.bounding_box()
                if box:
                    page.mouse.move(box["x"] + box["width"]/2, box["y"] + box["height"]/2, steps=10)
                page.locator(pass_selector).first.click()
                human_type(page, pass_selector, password)

                time.sleep(random.uniform(1, 2.5))
                page.click("button[type='submit']")

                try:
                    page.wait_for_load_state("networkidle", timeout=15000)
                except PWTimeout:
                    log.info("Network idle timeout during login. Checking URL/Captcha.")
                
                # Check for captcha or OTP
                if "captcha" in page.url.lower() or page.locator("text=OTP").count() > 0 or page.locator("text=Verify").count() > 0:
                    log.error("CAPTCHA or OTP detected. Exiting gracefully to avoid ban.")
                    page.screenshot(path="error_screenshot.png")
                    sys.exit(1)

                time.sleep(random.uniform(3, 6))
                
                # Save session state
                context.storage_state(path=SESSION_FILE)
                log.info("Session state saved.")
            else:
                log.info("Already logged in using session state!")

            # Step 2: Go to Profile
            log.info("Navigating to profile page...")
            page.goto("https://www.naukri.com/mnjuser/profile", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=20000)
            time.sleep(random.uniform(3, 5))

            simulate_reading(page)

            # Step 3: Click Edit Headline
            log.info("Opening Headline edit modal...")
            headline_edit_selectors = [
                "section[data-section='resumeHeadline'] .edit-button",
                "[data-section='resumeHeadline'] .icon.edit",
                "span.edit[title='Edit Resume Headline']",
                ".resumeHeadline .editIcon",
                "text=Resume Headline",
            ]

            clicked = False
            for selector in headline_edit_selectors:
                try:
                    el = page.locator(selector).first
                    if el.is_visible(timeout=3000):
                        box = el.bounding_box()
                        if box: page.mouse.move(box["x"] + 5, box["y"] + 5, steps=5)
                        el.click()
                        clicked = True
                        break
                except Exception:
                    continue
            
            if not clicked:
                try:
                    page.get_by_text("Resume Headline").locator("..").locator(".edit, .pencil, [class*='edit']").first.click()
                except Exception:
                    log.error("Could not find edit button.")
                    page.screenshot(path="error_screenshot.png")
                    sys.exit(1)

            time.sleep(random.uniform(1.5, 3))

            # Step 4: Clear and human type new headline
            log.info("Typing new headline...")
            headline_input_selectors = [
                 "input[placeholder*='headline' i]",
                 "textarea[placeholder*='headline' i]",
                 "input[name='resumeHeadline']",
                 "textarea[name='resumeHeadline']",
            ]
            
            typed = False
            for selector in headline_input_selectors:
                try:
                    el = page.locator(selector).first
                    if el.is_visible(timeout=3000):
                        el.triple_click()
                        time.sleep(0.5)
                        page.keyboard.press("Backspace")
                        time.sleep(0.5)
                        human_type(page, selector, new_headline)
                        typed = True
                        break
                except Exception:
                    continue

            if not typed:
                log.error("Could not find headline input field. Taking screenshot.")
                page.screenshot(path="error_screenshot.png")
                sys.exit(1)

            time.sleep(random.uniform(1.5, 3))

            # Step 5: Save
            log.info("Saving changes...")
            save_selectors = ["button:has-text('Save')", "button[type='submit']", ".saveBtn", "input[value='Save']"]
            for selector in save_selectors:
                try:
                    el = page.locator(selector).first
                    if el.is_visible(timeout=2000):
                        el.click()
                        break
                except Exception:
                    continue

            time.sleep(random.uniform(3, 5))

            log.info("✅ Profile updated successfully!")
            log.info(f"New headline set to: {new_headline}")
            page.screenshot(path="success_screenshot.png")

        except Exception as e:
            log.error(f"Failed at URL: {page.url}")
            log.error(f"Unexpected error: {str(e)}")
            page.screenshot(path="error_screenshot.png")
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    email = os.environ.get("NAUKRI_EMAIL")
    password = os.environ.get("NAUKRI_PASSWORD")

    if not email or not password:
        log.error("Missing credentials! Set NAUKRI_EMAIL and NAUKRI_PASSWORD.")
        sys.exit(1)

    update_naukri(email, password)
