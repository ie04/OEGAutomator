# pages/global_search.py
from playwright.async_api import Page, TimeoutError
from .selectors import CONTACTS_SECTION, CONTACT_LINKS





def contacts_section(page: Page):
    return page.locator(CONTACTS_SECTION)


def first_contact_link_in_section(section):
    return section.locator(CONTACT_LINKS).first


class GlobalSearch:
    def __init__(self, page: Page):
        self.page = page

    async def search(self, query: str) -> bool:
        page = self.page

        
        await page.wait_for_load_state("domcontentloaded")

        tabs = page.get_by_role("button", name="Close Tab")


        count = await tabs.count()
        for i in range(count):
            await tabs.nth(0).click()


        # 2) Find the global Search button safely
        search_btn = page.get_by_role("button", name="Search").first
        
        await search_btn.wait_for(state="attached")
        await search_btn.dblclick()

        # 3) Interact with the search box, with robust waiting
        sb = page.get_by_role("searchbox", name="Search...")
        await sb.wait_for(state="attached")
        await sb.fill(query)
        await sb.press("Enter")

        # 4) Wait for Contacts section to show results
        section = contacts_section(page)
        try:
            await section.wait_for(state="visible", timeout=5000)
        except TimeoutError:
            return False

        links = section.locator(CONTACT_LINKS)

        if await links.count() == 0:
            return False

        first_link = links.first
        await first_link.scroll_into_view_if_needed()
        await first_link.click()

        return True