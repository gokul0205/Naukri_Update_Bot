# Naukri Daily Profile Updater  

Automatically updates your Naukri resume headline daily via GitHub Actions —
keeping your profile "recently active" and boosting recruiter visibility.

---

## How It Works

Every day at **9:00 AM IST**, GitHub Actions:
1. Logs into your Naukri account
2. Edits your Resume Headline with a rotating suffix
3. Saves the change
4. Uploads a screenshot as proof

---

## Setup (5 minutes)

### 1. Fork / clone this repo to your GitHub

### 2. Add your Naukri credentials as GitHub Secrets

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**

| Secret Name      | Value                  |
|------------------|------------------------|
| `NAUKRI_EMAIL`   | your Naukri login email |
| `NAUKRI_PASSWORD`| your Naukri password    |

>  Secrets are encrypted — GitHub never exposes them in logs.

### 3. Edit your headline in `update_naukri.py`

Open `update_naukri.py` and update this line to match **your actual Naukri headline**:

```python
BASE_HEADLINE = "Data Engineer | Python | SQL | Spark | Cloud"
```

Also customize `SUFFIXES` list with whatever rotating text you want appended daily.

### 4. Enable GitHub Actions

Go to **Actions** tab in your repo → click **"I understand my workflows, go ahead and enable them"**

### 5. Test it manually

Go to **Actions → Daily Naukri Profile Updater → Run workflow** to trigger it immediately.

---

## Debugging

- Screenshots (`success_screenshot.png` / `error_screenshot.png`) are uploaded as **artifacts** after each run (kept for 3 days)
- `update.log` is committed to the repo after each run

---

## Customization

**Change the schedule** — edit the cron in `.github/workflows/update_naukri.yml`:
```yaml
- cron: "30 3 * * *"   # 9:00 AM IST (3:30 AM UTC)
```

Use [crontab.guru](https://crontab.guru) to generate cron expressions.

**Change what gets updated** — the script currently rotates the Resume Headline.
You can adapt it to update your Summary/About section instead.

---

## ⚠️ Notes

- This uses [Playwright](https://playwright.dev/) to control a real browser — same as a human clicking.
- Keep your suffixes professional — recruiters can see your headline.
- GitHub Actions is **free** for public repos, and free up to 2,000 min/month for private repos. This job runs in ~2 minutes daily.
