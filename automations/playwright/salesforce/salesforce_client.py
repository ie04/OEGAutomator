from urllib.parse import urlparse

from application.ports import SalesforcePort, StudentSnapshot
from playwright.async_api import Page
from ...config.settings import SalesforceSettings
from ..browser import BrowserSession
from .pages.auth import AuthFlow
from .pages.global_search import GlobalSearch
from .pages.contact_details import ContactDetails


class StudentNotFoundError(Exception):
    pass


class SalesforceClient(SalesforcePort):
    def __init__(self, sf_cfg: SalesforceSettings, session: BrowserSession):
        self.cfg = sf_cfg
        self.session = session

    async def fetch_student_snapshot(self, student_id: str) -> StudentSnapshot:
        base_url = str(self.cfg.base_salesforce_url)
        page: Page = await self.session.get_page()
        await page.wait_for_load_state("domcontentloaded")


        if not base_url in page.url:
            await page.goto(base_url, wait_until="domcontentloaded")


            await AuthFlow(page).login_if_needed(
                username=self.cfg.username,
                password=self.cfg.password
            )

            await page.wait_for_load_state("domcontentloaded")


        found = await GlobalSearch(page).search(student_id)
        if not found:
            raise StudentNotFoundError(
                f"No student found in Salesforce with ID {student_id}"
            )

        student_snapshot = await ContactDetails(page).scrape_contact_page(student_id)
        if student_snapshot is None:
            raise StudentNotFoundError(
                f"Student page opened but snapshot parsing failed (ID {student_id})"
            )

        return student_snapshot

    @staticmethod
    def _needs_auth(current_url: str, base_url: str) -> bool:
        """
        Return True when the browser was redirected away from the expected
        Salesforce Lightning location and authentication is likely required.
        """
        current = urlparse(current_url)
        base = urlparse(base_url)

        current_host = (current.netloc or "").lower()
        base_host = (base.netloc or "").lower()

        return current_host != base_host