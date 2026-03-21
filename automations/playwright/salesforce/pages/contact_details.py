import re
from datetime import datetime
from typing import Optional

import pdb

from playwright.async_api import Page, Locator
from application.ports import StudentSnapshot


DETAILS_TAB_PANEL = "#tab-1"
DETAILS_SECTION_CONTENT = "div.section-content.slds-section__content"
FIELD_CONTAINER = "div.slds-form-element.test-id__output-root"
LABEL_SELECTOR = ".test-id__field-label"


class ContactDetails:
    def __init__(self, page: Page):
        self.page = page

    async def scroll_find(self, locator: Locator) -> None:
        page = self.page

        try:
            await page.evaluate("window.scrollTo(0, 0)")

            while True:
                if await locator.is_visible():
                    return

                at_bottom = await page.evaluate(
                    "window.innerHeight + window.scrollY >= document.documentElement.scrollHeight"
                )
                if at_bottom:
                    break

                await page.mouse.wheel(0, 800)

            raise ValueError("Locator was not found before reaching the bottom of the page.")

        finally:
            await page.evaluate("window.scrollTo(0, 0)")

    async def get_student_details_value(self, label: str):
        page = self.page

        student_details = page.locator("div.section-layout-container").filter(
            has=page.get_by_role("button", name="Student Details", exact=True)
        ).first
        field_label = student_details.locator(".test-id__field-label", has_text=label).first
        field_row = field_label.locator("xpath=ancestor::div[contains(@class,'test-id__output-root')][1]")
        value_locator = field_row.locator(".test-id__field-value")
        
        await value_locator.wait_for(state="attached")

        try:
            value = (await value_locator.inner_text()).strip()
        except Exception as e: #if playwright fails to locate value
            raise ValueError(f'Field "{label}" is blank or not found') from e
        
        if value == "": #if value located is blank
            raise ValueError(f'Field "{label}" is blank or not found')
        
        return value
        
    async def get_student_email_value(self):

        async def ensure_contact_information_open(page: Page):
            contact_toggle = page.get_by_role("button", name="Contact Information", exact=True)
            await contact_toggle.scroll_into_view_if_needed()
            expanded = await contact_toggle.get_attribute("aria-expanded")
            if expanded == "false":
                await contact_toggle.click()

        page = self.page


        await ensure_contact_information_open(page)
        
        contact_section = page.locator("div.field-section2").filter(
            has=page.get_by_role("button", name="Contact Information", exact=True)
        )

        email_row = contact_section.locator('[data-field-id="RecordEmailField"]')

        email_link = email_row.locator('a[href^="mailto:"]').first

        #await self.scroll_find(email_link)


        try:    
            email = (await email_link.inner_text()).strip()
        except Exception as e: #if playwright fails to locate value
            raise ValueError(f'Field "Email" is blank or not found') from e
        
        if email == "": #if value located is blank
            raise ValueError(f'Field "Email" is blank or not found')
        
        return email

    async def scrape_contact_page(self, student_id: str) -> StudentSnapshot:
        page = self.page

        student = StudentSnapshot()
        
        contact_student_id = await self.get_student_details_value("CV StuNum")

        if contact_student_id != student_id:
            raise ValueError(f'User supplied Student ID "{student_id}" does not match contact page Student ID "{contact_student_id}". Automator on wrong contact page?"')
        else:
            student.student_id = student_id

        student_name = (await self.get_student_details_value("Name")).split()

        student.first_name = student_name[0]
        student.last_name = student_name[-1]

        student.dob = datetime.strptime(await self.get_student_details_value("Birthdate"), "%m/%d/%Y")
        student.ssn = await self.get_student_details_value("Social Security Number")
        student.enrollment_version_code = await self.get_student_details_value("Primary Program Enrollment Version Code")
        student.program_start_date = datetime.strptime(await self.get_student_details_value("Primary PE Exp Start Date"), "%m/%d/%Y") 
        student.email = await self.get_student_email_value()


        return student