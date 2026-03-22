# OEG Automator

Desktop automation suite for common OEG workflows:

- Salesforce student lookup
- NSLDS querying
- Batch adding Salesforce enrollment agreements
- Outlook email generation from templates
- Excel-based tuition breakdown generation

The app uses a Tkinter desktop UI, Playwright for browser automation, Outlook/Excel via `pywin32`, and a persistent Chrome profile for authenticated Salesforce and NSLDS sessions.

## What It Does

This repo bundles several internal productivity workflows into one Windows desktop app:

- `Load Student by Student ID`
  Loads a student from Salesforce and surfaces follow-up actions.
- `Query NSLDS`
  Uses the loaded student snapshot to pull NSLDS aid and enrollment information.
- `Send Email`
  Generates Outlook emails from `.oft` templates for missed contact, task list, and estimated financial aid workflows.
- `Generate Tuition Breakdown`
  Fills an Excel template, exports a PDF, and opens it in Adobe Acrobat.
- `Salesforce Helpers`
  Includes helper flows like batch adding enrollment agreements.

## Tech Stack

- Python 3.13
- Tkinter
- Playwright
- Pillow
- Pydantic / pydantic-settings
- pywin32
- lxml

## Environment Requirements

This project is Windows-focused and expects:

- Windows
- Google Chrome installed
- Microsoft Outlook installed
- Microsoft Excel installed
- Adobe Acrobat or Acrobat Reader installed

Tkinter ships with standard Python on Windows, so it does not appear in `requirements.txt`.

## Installation

1. Create and activate a virtual environment.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install Python dependencies.

```powershell
pip install -r requirements.txt
```

3. Install the Playwright browser integration used by the app.

```powershell
python -m playwright install chrome
```

## Configuration

Settings are loaded from `.env` via `pydantic-settings`.

Current environment variable groups:

- `BROWSER_*`
- `SF_*`
- `NSLDS_*`

Example:

```env
BROWSER_CHROME_CHANNEL=chrome
BROWSER_HEADLESS=false

SF_BASE_SALESFORCE_URL=https://fullsail2.lightning.force.com/
SF_USERNAME=your_username
SF_PASSWORD=your_password

NSLDS_BASE_URL=https://nsldsfap.ed.gov/
NSLDS_USERNAME=your_username
NSLDS_PASSWORD=your_password
```

Notes:

- The project uses a persistent Playwright Chrome profile under `automations/playwright/chrome_profile`.
- Some auth flows may still require Duo / MFA even with a persistent profile.

## Running The App

```powershell
python main.py
```

The app starts an `AutomationRunner` on a background thread and then launches the Tkinter UI.

## Project Structure

```text
application/
  ports.py
  services/

automations/
  runner.py
  config/
  playwright/
    browser.py
    salesforce/
    nslds/
    tests/
  tuition_breakdown_generator/
  email_generator/

ui/
  automator_ui.py
  pages/
  widgets/
```

## Debugging Salesforce / NSLDS Independently

The repo includes a long-lived Playwright debug harness so you can iterate without relaunching the full UI:

```powershell
python automations/playwright/tests/debug_salesforce_client.py salesforce 0005530036
```

or:

```powershell
python automations/playwright/tests/debug_salesforce_client.py nslds 0005530036
```

Useful files:

- `automations/playwright/tests/debug_salesforce_client.py`
- `automations/playwright/tests/salesforce_experiment.py`
- `automations/playwright/tests/nslds_experiment.py`

The harness keeps the Playwright browser session open and reloads experiment code between runs.

## Tests

There are lightweight unit-style tests for the Playwright client entry points:

```powershell
python -m unittest automations.playwright.tests.test_playwright_debug
```

## Important Notes

- This repo is tightly coupled to specific Salesforce and NSLDS UI flows.
- Outlook and Excel automations depend on local desktop applications being installed and available through COM.
- Tuition breakdown generation is Windows-only because it automates Excel directly.
- Playwright browser authentication behavior depends partly on site session policy, not only on the local Chrome profile.

## Recommended Git Hygiene

Before committing:

- avoid checking in `.env`
- avoid checking in changes inside the Playwright profile unless intentional
- keep generated outputs and local profile/session artifacts out of version control
