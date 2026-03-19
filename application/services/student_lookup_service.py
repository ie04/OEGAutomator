from automations.playwright.salesforce.salesforce_client import SalesforceClient
from application.ports import StudentSnapshot
from datetime import datetime

class StudentLookupService:
    def __init__(self, salesforce_client: SalesforceClient) -> None:
        self.salesforce_client = salesforce_client

    async def load_student(self, student_id: str) -> StudentSnapshot:

        student = await self.salesforce_client.fetch_student_snapshot(student_id)    
        student.is_dependent = self._is_dependent(student)

        return student
    
    def _is_dependent(self, student: StudentSnapshot) -> bool:
        if not isinstance(student.dob, datetime):
            raise TypeError("student.dob must be a date")

        today = datetime.today()
        award_year_start = today.year if today.month >= 7 else today.year - 1
        independence_cutoff = datetime(award_year_start - 23, 1, 1)

        is_independent = student.dob < independence_cutoff
        return not is_independent