from datetime import datetime

from application.ports import StudentSnapshot
from automations.playwright.browser import BrowserSession


async def run(clients, session: BrowserSession, student_id: str):
    """
    Default NSLDS experiment:
    1. Load the student snapshot from Salesforce using the student ID.
    2. Pass that snapshot into NSLDSClient.

    Edit this function freely while the debug harness is running.
    It is reloaded before every loop iteration.
    """
    nslds_client = clients["nslds"]
    dummy_student = StudentSnapshot(
        student_id="0005530036",
        first_name="Marco",
        last_name="Ramos",
        dob=datetime(1991, 7, 15, 0, 0),
        ssn="622-48-9345",
        enrollment_version_code="GDVAS01-O",
        program_start_date=datetime(2026, 4, 6, 0, 0),
        is_dependent=False,
        email="maramos1749@gmail.com",
    )

    _ = clients
    _ = session
    _ = student_id
    return await nslds_client.fetch_NSLDS_snapshot(dummy_student)
