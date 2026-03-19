# infrastructure/nslds/pages/auth.py
from playwright.async_api import Page

LOGIN_URL = "https://nsldsfap.ed.gov/login"
HOME_URL = "https://nsldsfap.ed.gov/home"
CAS_URL_AUTH = "https://sa.ed.gov/cas/CASWeb/pages/Authentication.faces"
CAS_URL_PA = "https://sa.ed.gov/cas/CASWeb/pages/PrivacyAct.faces"
CAS_URL_VIP = "https://sa.ed.gov/cas/CASWeb/pages/TFA/validation/Validate.faces"
CAS_URL_ROB = "https://sa.ed.gov/cas/CASWeb/pages/ROB.faces"

class AuthFlow:
    def __init__(self, page: Page):
        self.page = page

    async def login(self, username: str | None, password: str | None) -> None:
        page = self.page


        await page.wait_for_load_state("networkidle")

        if page.url.startswith(HOME_URL):
            return

        if page.url.startswith(LOGIN_URL):
            login_link = page.get_by_role("link", name="Log In", exact=True)

            await login_link.wait_for(state="attached", timeout=30000)
            
            if await login_link.count() > 0:
                await login_link.click()
                await page.wait_for_url(CAS_URL_AUTH)
                
        
        if page.url.startswith(CAS_URL_AUTH):
            user_box = page.get_by_role("textbox", name="* User ID:")
            if await user_box.count() > 0:
                await user_box.fill(username)

            pwd_box = page.get_by_role("textbox", name="* Password:")
            if await pwd_box.count() > 0:
                await pwd_box.fill(password)

            login_btn = page.get_by_role("button", name="Log In")
            if await login_btn.count() > 0:
                await login_btn.click()
                await page.wait_for_url(CAS_URL_PA)
                

        if page.url.startswith(CAS_URL_PA):
            confirm_checkbox = page.get_by_role("checkbox", name="I confirm that I am an")
            if await confirm_checkbox.count() > 0:
                await confirm_checkbox.check()

            continue_btn = page.get_by_role("button", name="CONTINUE")
            if await continue_btn.count() > 0:
                await continue_btn.click()
                await page.wait_for_url(CAS_URL_VIP)
                

        if page.url.startswith(CAS_URL_VIP):
            code_box = page.get_by_role("textbox", name="* Security Code:")
            if await code_box.count() > 0:
                while True:
                    vip_code = input("Enter VIP Access code: ")
                    await code_box.fill(vip_code)

                    validate_btn = page.get_by_role("button", name="Validate")
                    if await validate_btn.count() > 0:
                        await validate_btn.click()
                        await page.wait_for_load_state("networkidle")

                    

                    if page.url.startswith(CAS_URL_ROB):
                        checkbox = page.get_by_role("checkbox", name="I acknowledge receipt of")
                        if await checkbox.count() > 0:
                            await checkbox.click()
                            
                            accept_btn = page.get_by_role("button", name="Accept")
                            if await accept_btn.count() > 0:
                                await accept_btn.click()

                            await page.wait_for_load_state("networkidle")


                    await page.wait_for_url(HOME_URL)
                    

                    if page.url.startswith(HOME_URL):
                        break
                    else:
                        error = page.get_by_text("Please enter a valid Security")
                        if error.count() > 0:
                            print("Error: Invalid VIP Access code, try again...")
                            continue
