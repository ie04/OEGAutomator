from urllib.parse import urlparse
from typing import List, Optional
from pathlib import Path
from datetime import date
import re

from application.ports import SalesforcePort, StudentSnapshot
from playwright.async_api import Page, Locator, expect
from ...config.settings import SalesforceSettings
from ..browser import BrowserSession
from .pages.auth import AuthFlow
from .pages.global_search import GlobalSearch
from .pages.contact_details import ContactDetails

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CAEA_DIRECTORY = PROJECT_ROOT / "automations" / "playwright" / "salesforce" / "CAEA"

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

    async def batch_add_enrollment_agreements(self, id_list: List[str]) -> bool:

        async def get_earliest_date_row(page: Page) -> Optional[Locator]:
            rows = page.locator('tr[role="row"]')

            # Guard that at least the first matched row is attached.
            await expect(rows.first).to_be_attached()

            row_count = await rows.count()
            earliest_date_row: Optional[Locator] = None
            earliest_date: Optional[date] = None

            for i in range(row_count):
                row = rows.nth(i)
                await expect(row).to_be_attached(timeout=30000)

                date_element = row.locator("lightning-base-formatted-text").filter(has_text=re.compile(r"-")).first
                if await date_element.is_visible():
                    text = (await date_element.inner_text()).strip()
                else:
                    continue


                match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)

                if not match:
                    continue

                current_date = date.fromisoformat(match.group(0))

                if earliest_date is None or current_date < earliest_date:
                    earliest_date = current_date
                    earliest_date_row = row

            return earliest_date_row
        
        enrollment_agreement_tool_url = f"https://fullsail2.lightning.force.com/lightning/n/Enrollment_Agreement_Tool"
        base_url = str(self.cfg.base_salesforce_url)
        page = await self.session.get_page()

        if not enrollment_agreement_tool_url in page.url:

            await page.goto(enrollment_agreement_tool_url, wait_until="load")

            if not enrollment_agreement_tool_url in page.url:

                await AuthFlow(page).login_if_needed(
                    username=self.cfg.username,
                    password=self.cfg.password
                )

                await page.goto(enrollment_agreement_tool_url, wait_until="load")

        filter_id_box = page.get_by_role("searchbox", name="Search Filter")
        filter_id_btn = page.get_by_role("button", name="Filter Enrollments")
        await expect(filter_id_box).to_be_visible()
        await expect(filter_id_btn).to_be_visible()
        
        
        for id in id_list:

            await filter_id_box.fill(id)
            await filter_id_btn.click()

            earliest_date_row = await get_earliest_date_row(page)

            already_assigned_date = earliest_date_row.locator("lightning-formatted-date-time")
            await expect(already_assigned_date).to_be_attached()

            if await already_assigned_date.inner_text() != "":
                print(f"EA doc(s) for student id {id} already added")
                continue

            select_student_btn = earliest_date_row.locator(".slds-radio_faux")
            await expect(select_student_btn).to_be_visible()
            await select_student_btn.click()

            assign_ea_btn = page.get_by_role("button", name="Assign Custom Document")
            await expect(assign_ea_btn).to_be_visible()

            if await assign_ea_btn.is_enabled():
                await assign_ea_btn.click()
            else:
                print(f"Unable to assign EA for student id {id} ('Assign Custom Document is greyed out')")
                continue

            doc_type_box = page.get_by_role("combobox", name="Document Type")
            await expect(doc_type_box).to_be_visible()
            await doc_type_box.click()
            await expect(doc_type_box).to_have_attribute("aria-expanded", "true")

            details_table = page.locator("dl.slds-list_horizontal")
            await expect(details_table).to_be_visible()



            program_version_code = (await page.get_by_title("CV Program Version Code")
                                    .locator("xpath=following-sibling::dd[1]")
                                    .text_content() or "").strip()  
            
            program_cost = (await page.get_by_title("CV Program Cost")
                            .locator("xpath=following-sibling::dd[1]")
                            .text_content() or "").strip().replace("\r", "").replace("\n", "")
            
            start_date = (await page.get_by_title("Start Date")
                        .locator("xpath=following-sibling::dd[1]")
                        .text_content() or "").strip()
            
            EA_option = page.get_by_role("option", name=re.compile(r"AMENRAG[AB]"))
            CAEA_option = page.get_by_role("option", name="AMCAEAAD")

            await expect(EA_option).to_be_visible()

            CAEA_needed = await CAEA_option.count() > 0

            await EA_option.click()

            doc_template_box = page.get_by_placeholder("Select Document Template")
            await expect(doc_template_box).to_be_enabled()
            await doc_template_box.click()
            listbox = page.get_by_role("listbox")
            await expect(listbox).to_be_visible()

            await doc_template_box.press_sequentially(program_version_code, delay=50)

            program_selection = page.get_by_role("option", name=f"{start_date}:{program_version_code}")
            await expect(program_selection).to_be_attached()
            await program_selection.scroll_into_view_if_needed()
            await expect(program_selection).to_be_visible()
            await program_selection.click()

            submit_btn = page.get_by_role("button", name="Submit")
            await expect(submit_btn).to_be_enabled()
            await submit_btn.click()
            await expect(submit_btn).not_to_be_visible(timeout=30000)


            if CAEA_needed:
                await select_student_btn.click()
                await expect(assign_ea_btn).to_be_enabled()
                await assign_ea_btn.click()

                await expect(doc_type_box).to_be_visible()
                await doc_type_box.click()

                await expect(CAEA_option).to_be_visible()
                await CAEA_option.click()

                file_input = page.locator('input[type="file"][accept=".pdf"][name="pdfUploader"]')
                await file_input.scroll_into_view_if_needed()

                await file_input.set_input_files(str(CAEA_DIRECTORY / f"AMCAEAAD {program_cost}.pdf"))
                done_btn = page.get_by_role("button", name="Done")
                await expect(done_btn).to_be_enabled(timeout=30000)
                await done_btn.click()
                await expect(page.get_by_text("File uploaded:")).to_be_attached()

                await expect(submit_btn).to_be_enabled()
                await submit_btn.click()
                await expect(submit_btn).not_to_be_visible(timeout=30000)

            if CAEA_needed:    
                print(f"EA & CAEA successfully added for student id {id}")
            else:
                print(f"EA successfully added for student id {id}")




            


           
            
            



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