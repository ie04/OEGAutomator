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

        load_element = page.get_by_role("tab", name="Details")

        try:
            await load_element.first.wait_for(state="visible", timeout=3000)
        except Exception:
            pass

        tabs = page.get_by_role("button", name="Close Tab")

        if await tabs.first.is_visible(timeout=10000):
            count = await tabs.count()
        else:
            count = 0

        for i in range(count):
            await tabs.nth(0).click()


        # 2) Find the global Search button safely
        search_btn = page.get_by_role("button", name="Search").first
        sb = page.get_by_role("searchbox", name="Search...")

        await search_btn.wait_for(state="visible", timeout=3000)
        await search_btn.dblclick()

        await sb.wait_for(state="attached", timeout=3000)
        await sb.fill(query)
        await sb.press("Enter")
                

        

        # 4) Wait for Contacts section to show results
        section = contacts_section(page)
        try:
            await section.wait_for(state="visible", timeout=5000)
        except TimeoutError:
            return False

        links = section.locator(CONTACT_LINKS)

        if await links.first.is_visible(timeout=3000):
            if await links.count() == 0:
                return False

        await links.first.scroll_into_view_if_needed()
        await links.first.click()

        return True