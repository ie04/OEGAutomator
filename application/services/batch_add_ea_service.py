from collections.abc import Callable

from automations.playwright.salesforce.salesforce_client import SalesforceClient


class BatchAddEAService:
    def __init__(self, salesforce_client: SalesforceClient) -> None:
        self.salesforce_client = salesforce_client

    async def run(
        self,
        student_ids: list[str],
        log: Callable[[str], None] | None = None,
    ) -> bool:
        return await self.salesforce_client.batch_add_enrollment_agreements(
            student_ids,
            log=log,
        )
