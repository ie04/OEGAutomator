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


def load_nslds_client_class():
    auth_module = importlib.import_module(
        "automations.playwright.nslds.pages.auth"
    )
    pull_module = importlib.import_module(
        "automations.playwright.nslds.pages.pull_up_student"
    )
    aid_module = importlib.import_module(
        "automations.playwright.nslds.pages.aid_page"
    )
    enrollment_module = importlib.import_module(
        "automations.playwright.nslds.pages.enrollment_page"
    )
    client_module = importlib.import_module(
        "automations.playwright.nslds.nslds_client"
    )

    importlib.reload(auth_module)
    importlib.reload(pull_module)
    importlib.reload(aid_module)
    importlib.reload(enrollment_module)
    client_module = importlib.reload(client_module)

    return client_module.NSLDSClient


def load_experiment_module(experiment_name: str):
    module = importlib.import_module(
        f"automations.playwright.tests.{experiment_name}_experiment"
    )
    return importlib.reload(module)


async def run_current_experiment(
    session: BrowserSession,
    student_id: str,
    experiment_name: str,
) -> None:
    settings = get_settings()
    SalesforceClient = load_salesforce_client_class()
    NSLDSClient = load_nslds_client_class()
    clients = {
        "salesforce": SalesforceClient(settings.salesforce, session),
        "nslds": NSLDSClient(settings.nslds, session),
    }
    experiment_module = load_experiment_module(experiment_name)
    result = await experiment_module.run(
        clients=clients,
        session=session,
        student_id=student_id,
    )
    if result is not None:
        print("\nResult:")
        print(result)


async def main(experiment_name: str, student_id: str) -> None:
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
        current_experiment = experiment_name

        while True:
            print(
                f"\nRunning {current_experiment} experiment with student ID: "
                f"{current_student_id}"
            )

            try:
                await run_current_experiment(
                    session=session,
                    student_id=current_student_id,
                    experiment_name=current_experiment,
                )
            except Exception as exc:
                print(f"\nRun failed: {exc}")

            print("\nPlaywright Inspector is opening on the current page.")
            print("Resume it when you're ready to rerun your updated code.\n")
            await page.pause()

            next_action = input(
                "Press Enter to rerun, type a new student ID, type "
                "'salesforce' or 'nslds' to switch experiments, or type 'q' to quit: "
            ).strip()

            if next_action.lower() in {"q", "quit", "exit"}:
                break

            if next_action.lower() in {"salesforce", "nslds"}:
                current_experiment = next_action.lower()
                continue

            if next_action:
                current_student_id = next_action
    finally:
        await session.stop()


if __name__ == "__main__":
    args = [arg.strip() for arg in sys.argv[1:]]

    if len(args) == 1 and args[0]:
        experiment_name = "salesforce"
        student_id = args[0]
    elif len(args) == 2 and args[0].lower() in {"salesforce", "nslds"} and args[1]:
        experiment_name = args[0].lower()
        student_id = args[1]
    else:
        raise SystemExit(
            "Usage: python automations/playwright/tests/debug_salesforce_client.py "
            "[salesforce|nslds] <student_id>"
        )

    asyncio.run(main(experiment_name, student_id))
