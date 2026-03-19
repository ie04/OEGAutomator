from playwright.async_api import Page
from application.ports import AuditSnapshot, RedFlagCode, RedFlag

ENR_URL = "https://nsldsfap.ed.gov/aid-recipient/enrollment"
class EnrollmentPage:
    def __init__(self, page: Page):
        self.page = page

    async def scrape_enrollment_page(self, aid: AuditSnapshot):
        page = self.page

        await page.goto(ENR_URL)
        await page.wait_for_load_state("networkidle")


        if await page.get_by_text("No enrollment data exists for").is_visible():
            return
        
        await page.wait_for_selector("table[aria-label^='The enrollment summary table']")

        # Find "Most Recent Status" header and its column index (0-based within the row)
        status_header = page.get_by_role("columnheader", name="Most Recent Status")
        col_index = await status_header.evaluate(
            "(el) => Array.from(el.parentElement.children).indexOf(el)"
        )

        # School Name is one column to the left
        school_col = col_index - 1

        rows = page.locator(
            "table[aria-label^='The enrollment summary table'] tbody.p-datatable-tbody tr"
        )
        row_count = await rows.count()

        for i in range(row_count):
            row = rows.nth(i)

            # Status cell for this row
            status_cell = row.locator("td").nth(col_index)
            status_text = (await status_cell.inner_text()).strip()

            if not status_text:
                continue

            school_cell = row.locator("td").nth(school_col)
            school_name = (await school_cell.inner_text()).strip()

            match status_text[0]:
                case "F":
                    aid.append_red_flag(RedFlagCode.DUAL_ENROLLMENT_FT, school_name)
                
                case "Q":
                    aid.append_red_flag(RedFlagCode.DUAL_ENROLLMENT_TQT, school_name)

                case "H":
                    aid.append_red_flag(RedFlagCode.DUAL_ENROLLMENT_HT, school_name)
                
                case "Z": 
                    aid.append_red_flag(RedFlagCode.DUAL_ENROLLMENT_NRF, school_name)

                case _:
                    pass
                