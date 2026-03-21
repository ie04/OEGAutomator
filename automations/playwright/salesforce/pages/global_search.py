# pages/global_search.py
from playwright.async_api import Page, TimeoutError, expect
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

        tablist = page.get_by_label("Workspace tabs for Student")
        await expect(tablist).to_be_visible()

        tabs = tablist.get_by_role("button").filter(has_text="Close")
        count = await tabs.count()
        for i in range(count):
            await tabs.nth(0).click()


        # 2) Find the global Search button safely
        search_btn = page.get_by_role("button", name="Search", exact=True)
        

        await expect(search_btn).to_be_visible()
        await expect(search_btn).to_be_enabled()
        await search_btn.scroll_into_view_if_needed()
        await search_btn.hover()
        await search_btn.click()
        
        dialog = page.get_by_role("dialog", name="Search...")
        await expect(dialog).to_be_visible()

        sb = page.get_by_role("searchbox", name="Search...")
        await expect(sb).to_be_visible()
        await sb.fill(query)
        await sb.press("Enter")
                

        
        rows = page.locator("tr")
        count = await rows.count()

        # 4) Wait for Contacts section to show results
        section = page.locator(CONTACTS_SECTION)
        await expect(section).to_be_visible()

        links = section.locator(CONTACT_LINKS)
        await expect(links.first).to_be_visible(timeout=30000)
        if await links.count() == 0:
            return False

        await links.first.scroll_into_view_if_needed()
        await links.first.click()

        return True