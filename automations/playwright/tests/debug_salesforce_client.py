import asyncio
import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from automations.config.settings import get_settings
from automations.playwright.browser import BrowserSession


def load_salesforce_client_class():
    auth_module = importlib.import_module(
        "automations.playwright.salesforce.pages.auth"
    )
    search_module = importlib.import_module(
        "automations.playwright.salesforce.pages.global_search"
    )
    details_module = importlib.import_module(
        "automations.playwright.salesforce.pages.contact_details"
    )
    client_module = importlib.import_module(
        "automations.playwright.salesforce.salesforce_client"
    )

    importlib.reload(auth_module)
    importlib.reload(search_module)
    importlib.reload(details_module)
    client_module = importlib.reload(client_module)

    return client_module.SalesforceClient


def load_experiment_module():
    module = importlib.import_module(
        "automations.playwright.tests.salesforce_experiment"
    )
    return importlib.reload(module)


async def run_current_experiment(session: BrowserSession, student_id: str) -> None:
    settings = get_settings()
    SalesforceClient = load_salesforce_client_class()
    client = SalesforceClient(settings.salesforce, session)
    experiment_module = load_experiment_module()
    result = await experiment_module.run(client=client, session=session, student_id=student_id)
    if result is not None:
        print("\nResult:")
        print(result)


async def main(student_id: str) -> None:
    settings = get_settings()

    session = BrowserSession(
        user_data_dir=str(settings.browser.chrome_profile),
        channel=settings.browser.chrome_channel,
        headless=False,
    )

    await session.start()
    try:
        page = await session.get_page()
        current_student_id = student_id

        while True:
            print(f"\nRunning SalesforceClient with student ID: {current_student_id}")

            try:
                await run_current_experiment(session, current_student_id)
            except Exception as exc:
                print(f"\nRun failed: {exc}")

            print("\nPlaywright Inspector is opening on the current Salesforce page.")
            print("Resume it when you're ready to rerun your updated code.\n")
            await page.pause()

            next_action = input(
                "Press Enter to rerun, type a new student ID, or type 'q' to quit: "
            ).strip()

            if next_action.lower() in {"q", "quit", "exit"}:
                break
            if next_action:
                current_student_id = next_action
    finally:
        await session.stop()


if __name__ == "__main__":
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        raise SystemExit(
            "Usage: python automations/playwright/tests/debug_salesforce_client.py <student_id>"
        )

    asyncio.run(main(sys.argv[1].strip()))
