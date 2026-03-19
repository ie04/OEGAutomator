from playwright.sync_api import sync_playwright
import sys
from pathlib import Path
from automations.config.settings import SalesforceSettings

PROFILE_DIR = Path(__file__).resolve().parents[1] / "chrome_profile"

sf = SalesforceSettings()

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        channel="chrome",
        headless=False
    )

    page = context.pages[0] if context.pages else context.new_page()
    page.goto(sf.base_salesforce_url)

    print("\nBrowser ready.")
    print("1) Use Playwright Inspector")
    print("2) Resume script")
    print("3) Python debugger opens\n")

    # Inspector mode
    page.pause()

    print("\nEntering Python debugger (pdb).")
    print("Objects available: page, context\n")

    # Python REPL mode
    breakpoint()

    context.close()