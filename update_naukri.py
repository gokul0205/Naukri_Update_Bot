"""
Naukri Profile Updater — GitHub Actions (headless)
────────────────────────────────────────────────────
Production version: reads credentials from env vars / GitHub Secrets,
runs the same logic as test_local.py but in headless mode.

Env vars required:
    NAUKRI_EMAIL
    NAUKRI_PASSWORD
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from test_local import run

if __name__ == "__main__":
    email    = os.environ.get("NAUKRI_EMAIL", "").strip()
    password = os.environ.get("NAUKRI_PASSWORD", "").strip()

    if not email or not password:
        raise ValueError(
            "Missing credentials!\n"
            "Set NAUKRI_EMAIL and NAUKRI_PASSWORD as GitHub Secrets."
        )

    run(email=email, password=password, headless=True)