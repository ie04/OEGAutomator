from automations.playwright.browser import BrowserSession
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
IDS = PROJECT_ROOT / "automations" / "playwright" / "tests" / "ids.txt"

async def run(clients, session: BrowserSession, student_id: str):
    """
    Edit this function freely while the debug harness is running.
    It is reloaded before every loop iteration, so code changes here
    are picked up without restarting the browser session.
    """
    path = IDS
    with path.open("r", encoding="utf-8") as f:
        id_list: list[str] = [line.strip() for line in f if line.strip()]

    client = clients["salesforce"]
    _ = id_list
    _ = session
    return await client.fetch_student_snapshot(student_id)
