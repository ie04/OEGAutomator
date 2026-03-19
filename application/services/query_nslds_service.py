from automations.playwright.nslds.nslds_client import NSLDSClient
from application.ports import NSLDSSnapshot, StudentSnapshot


class QueryNSLDSService:
    def __init__(self, nslds_client: NSLDSClient) -> None:
        self.nslds_client = nslds_client

    async def query_nslds(self, student: StudentSnapshot) -> NSLDSSnapshot:
        return await self.nslds_client.fetch_NSLDS_snapshot(student)
