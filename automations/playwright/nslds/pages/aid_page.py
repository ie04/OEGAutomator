from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from application.ports import AuditSnapshot

DASHBOARD_URL = "https://nsldsfap.ed.gov/aid-recipient/dashboard"


class AidPage:
    def __init__(self, page: Page):
        self.page = page
    
    async def scrape_aid_page(self, aid_snapshot: AuditSnapshot):
        page = self.page

        await page.wait_for_url(DASHBOARD_URL)
        await page.wait_for_load_state("networkidle")
        
        locator = page.locator("span").filter(has_text="%").first

        try:
            await locator.wait_for(state="attached", timeout=2000)
        except PlaywrightTimeoutError:
            pass

        if await locator.count() > 0:
            await locator.scroll_into_view_if_needed()
            aid_snapshot.has_fa_history = True
            aid_snapshot.pell_leu = await locator.first.text_content()

        locator = page.get_by_text("No Aggregate Loan information")
        if await locator.count() > 0:
            return
        
        locator = page.get_by_role("cell", name="$").first

        if await locator.count() > 0:
            await locator.scroll_into_view_if_needed()
            text = await locator.first.text_content()
            aid_snapshot.sub_stafford_amount = float(text.translate(str.maketrans("","", "$,")))
        
        locator = page.get_by_role("cell", name="$").nth(4)

        if await locator.count() > 0:
            await locator.scroll_into_view_if_needed()
            text = await locator.text_content()
            aid_snapshot.total_stafford_amount = float(text.translate(str.maketrans("","", "$,")))

        
        


        




        


        
        
        
