from __future__ import annotations

import asyncio
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import Page

class AuthFlow:
    def __init__(self, page: Page):
        self.page = page

    async def login_if_needed(self, username: str, password: str) -> None:
        page = self.page
        lightning_pattern = "**/fullsail2.lightning.force.com/**"

        async def at_lightning() -> bool:
            return page.url.startswith("https://fullsail2.lightning.force.com/")

        async def auth0_button_visible() -> bool:
            auth0_btn = page.get_by_role("button", name="Log in with Auth0")
            try:
                await auth0_btn.wait_for(state="visible", timeout=3000)
                return True
            except PlaywrightTimeoutError:
                return False

        async def auth0_login_visible() -> bool:
            user_box = page.get_by_role("textbox", name="User name")
            try:
                await user_box.wait_for(state="visible", timeout=3000)
                return True
            except PlaywrightTimeoutError:
                return False

        async def duo_skip_visible() -> bool:
            skip_link = page.get_by_role("link", name="Skip for now")
            try:
                await skip_link.wait_for(state="visible", timeout=3000)
                return True
            except PlaywrightTimeoutError:
                return False

        async def wait_for_any_known_state(timeout_ms: int = 15000) -> str:
            """
            Wait until one of the known checkpoints appears:
            - active Salesforce session already at lightning
            - Salesforce login page with Auth0 button
            - Auth0 username field
            - Duo page with 'Skip for now'
            """
            deadline = asyncio.get_running_loop().time() + (timeout_ms / 1000)

            while True:
                if await at_lightning():
                    return "lightning"

                if await auth0_button_visible():
                    return "salesforce_login"

                if await auth0_login_visible():
                    return "auth0_login"

                if "duosecurity.com" in page.url:
                    # Could be Duo with or without Skip for now.
                    return "duo"

                if asyncio.get_running_loop().time() >= deadline:
                    raise RuntimeError(f"Timed out waiting for known login state. Current URL: {page.url}")

                await page.wait_for_timeout(250)

        state = await wait_for_any_known_state()

        while state != "lightning":
            if state == "salesforce_login":
                auth0_btn = page.get_by_role("button", name="Log in with Auth0")
                await auth0_btn.click()

                # After click, do not inspect URL immediately.
                # Wait for the next known page/state.
                state = await wait_for_any_known_state()
                continue

            if state == "auth0_login":
                user_box = page.get_by_role("textbox", name="User name")
                pwd_box = page.get_by_role("textbox", name="Password")
                login_btn = page.get_by_role("button", name="Log In")

                await user_box.wait_for(state="visible")
                await pwd_box.wait_for(state="visible")
                await login_btn.wait_for(state="visible")

                await user_box.fill(username)
                await pwd_box.fill(password)
                await login_btn.click()

                # After Auth0 submit, you may go to Duo or straight to lightning.
                state = await wait_for_any_known_state(timeout_ms=20000)
                continue

            if state == "duo":
                skip_link = page.get_by_role("link", name="Skip for now")

                # Sometimes Duo shows "Skip for now", sometimes it waits for phone approval.
                if await duo_skip_visible():
                    await skip_link.click()

                # Then wait for either lightning or for Duo to remain pending until approval completes.
                try:
                    await page.wait_for_url(lightning_pattern, timeout=60000)
                    state = "lightning"
                except PlaywrightTimeoutError:
                    # Still not back at lightning; re-check current page state.
                    state = await wait_for_any_known_state(timeout_ms=60000)

                continue

            raise RuntimeError(f"Unhandled login state: {state}")

        await page.wait_for_url(lightning_pattern)