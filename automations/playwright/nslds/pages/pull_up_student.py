from playwright.async_api import Page
from application.ports import StudentSnapshot, AuditSnapshot

DASHBOARD_URL = "https://nsldsfap.ed.gov/aid-recipient/dashboard"
HOME_URL = "https://nsldsfap.ed.gov/home"

class PullUpStudent:
    def __init__(self, page: Page):
        self.page = page
    
    async def search(self, student: StudentSnapshot) -> AuditSnapshot:
        page = self.page

        await page.wait_for_url(HOME_URL)

        # 1) Get and click "Search Aid Recipient" only if it exists
        search_aid_btn = page.get_by_role("button", name="Search Aid Recipient")
        if await search_aid_btn.count() > 0:
            await search_aid_btn.click()

        await page.wait_for_load_state("networkidle") #for Load in between clicking search

        # 2) Fill the search form using stable locators
        ssn_box = page.get_by_role("textbox", name="SSN")
        dob_box = page.get_by_role("textbox", name="Date of Birth")
        first_name_box = page.get_by_role("textbox", name="First Name")

        await page.get_by_role("button", name="Clear", exact=True).click()

        await ssn_box.fill(student.ssn)
        await dob_box.fill(student.dob.strftime("%m/%d/%Y"))
        await first_name_box.fill(student.first_name)

        search_btn = page.get_by_role("button", name="Search", exact=True)
        await search_btn.click()

        await page.wait_for_load_state("networkidle")

        # 3) Check post-search messages using guarded locators
        no_results_msg = page.get_by_text("No results were found.")
        no_aid_msg = page.get_by_text("There is no Aid reported for")

        if await no_results_msg.count() > 0:
            return AuditSnapshot(has_fa_history=False)
        
        if await no_aid_msg.count() > 0:
            return AuditSnapshot(has_fa_history=False)
        
        await page.wait_for_url(DASHBOARD_URL)
        await page.wait_for_load_state("networkidle")

        no_loans_msg = page.get_by_text("No Aggregate Loan information available")
        no_pell = page.get_by_text("N/R")

        if await no_loans_msg.count() > 0 and await no_pell.count() > 0:
            return AuditSnapshot(has_fa_history=False)
        
        return AuditSnapshot(has_fa_history=True)
