import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from application.ports import StudentSnapshot
from automations.playwright.salesforce.salesforce_client import (
    SalesforceClient,
    StudentNotFoundError,
)


class SalesforceClientUnitTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_student_snapshot_logs_in_when_page_is_not_at_salesforce(self):
        cfg = MagicMock()
        cfg.base_salesforce_url = "https://fullsail2.lightning.force.com/"
        cfg.username = "user@example.com"
        cfg.password = "secret"

        page = AsyncMock()
        page.url = "https://login.example.com/"
        page.wait_for_load_state = AsyncMock()
        page.goto = AsyncMock()

        session = MagicMock()
        session.get_page = AsyncMock(return_value=page)

        expected_snapshot = StudentSnapshot(student_id="1234567890")

        with (
            patch(
                "automations.playwright.salesforce.salesforce_client.AuthFlow"
            ) as auth_flow_cls,
            patch(
                "automations.playwright.salesforce.salesforce_client.GlobalSearch"
            ) as search_cls,
            patch(
                "automations.playwright.salesforce.salesforce_client.ContactDetails"
            ) as contact_cls,
        ):
            auth_flow = auth_flow_cls.return_value
            auth_flow.login_if_needed = AsyncMock()

            search = search_cls.return_value
            search.search = AsyncMock(return_value=True)

            contact = contact_cls.return_value
            contact.scrape_contact_page = AsyncMock(return_value=expected_snapshot)

            client = SalesforceClient(cfg, session)
            snapshot = await client.fetch_student_snapshot("1234567890")

        self.assertIs(snapshot, expected_snapshot)
        page.goto.assert_awaited_once_with(
            "https://fullsail2.lightning.force.com/",
            wait_until="domcontentloaded",
        )
        auth_flow.login_if_needed.assert_awaited_once_with(
            username="user@example.com",
            password="secret",
        )
        search.search.assert_awaited_once_with("1234567890")
        contact.scrape_contact_page.assert_awaited_once_with("1234567890")

    async def test_fetch_student_snapshot_raises_when_student_is_not_found(self):
        cfg = MagicMock()
        cfg.base_salesforce_url = "https://fullsail2.lightning.force.com/"

        page = AsyncMock()
        page.url = "https://fullsail2.lightning.force.com/lightning/page/home"
        page.wait_for_load_state = AsyncMock()
        page.goto = AsyncMock()

        session = MagicMock()
        session.get_page = AsyncMock(return_value=page)

        with patch(
            "automations.playwright.salesforce.salesforce_client.GlobalSearch"
        ) as search_cls:
            search = search_cls.return_value
            search.search = AsyncMock(return_value=False)

            client = SalesforceClient(cfg, session)

            with self.assertRaises(StudentNotFoundError):
                await client.fetch_student_snapshot("1234567890")

        page.goto.assert_not_awaited()

    def test_needs_auth_returns_false_for_same_host(self):
        self.assertFalse(
            SalesforceClient._needs_auth(
                "https://fullsail2.lightning.force.com/lightning/page/home",
                "https://fullsail2.lightning.force.com/",
            )
        )

    def test_needs_auth_returns_true_for_different_host(self):
        self.assertTrue(
            SalesforceClient._needs_auth(
                "https://idp.example.com/login",
                "https://fullsail2.lightning.force.com/",
            )
        )


if __name__ == "__main__":
    unittest.main()
