import asyncio
from typing import Optional, List
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright


class BrowserSession:
    def __init__(
        self,
        user_data_dir: str,
        channel: str = "chrome",
        headless: bool = False,
    ):
        self.user_data_dir = user_data_dir
        self.channel = channel
        self.headless = headless

        self._pw: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        self._pages: List[Page] = []

        self._lock = asyncio.Lock()
        self._closed_event = asyncio.Event()
        self._started = False

    @property
    def started(self) -> bool:
        return self._started and self.context is not None

    @property
    def is_closed(self) -> bool:
        return self._closed_event.is_set()

    async def start(self) -> None:
        if self.started:
            return

        self._closed_event.clear()
        self._pw = await async_playwright().start()
        self.context = await self._pw.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            channel=self.channel,
            headless=self.headless,
        )
        self.context.on("close", lambda: self._handle_context_closed())

        browser = self.context.browser
        if browser is not None:
            browser.on("disconnected", lambda: self._handle_context_closed())

        self._pages = list(self.context.pages)
        self._started = True

    async def stop(self) -> None:
        for p in list(self._pages):
            try:
                if not p.is_closed():
                    await p.close()
            except Exception:
                pass
        self._pages.clear()

        if self.context:
            try:
                await self.context.close()
            finally:
                self.context = None

        if self._pw:
            try:
                await self._pw.stop()
            finally:
                self._pw = None

        self._closed_event.set()
        self._started = False

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.stop()

    async def new_page(self) -> Page:
        if not self.started:
            raise RuntimeError("BrowserSession not started.")

        async with self._lock:
            page = await self.context.new_page()
            self._pages.append(page)
            return page

    async def get_page(self) -> Page:
        """
        Return the existing primary page if available.
        If no page exists yet, create one and keep it as the primary page.
        """
        if not self.started:
            raise RuntimeError("BrowserSession not started.")

        async with self._lock:
            live_tracked_pages = [p for p in self._pages if not p.is_closed()]
            if live_tracked_pages:
                self._pages = live_tracked_pages
                return live_tracked_pages[0]

            live_context_pages = [p for p in self.context.pages if not p.is_closed()]
            if live_context_pages:
                self._pages = live_context_pages
                return live_context_pages[0]

            page = await self.context.new_page()
            self._pages = [page]
            return page

    async def get_or_create_page(self) -> Page:
        return await self.get_page()

    async def close_extra_pages(self) -> None:
        """
        Keep only one live page open. Useful if jobs accidentally open extras.
        """
        if not self.started:
            raise RuntimeError("BrowserSession not started.")

        async with self._lock:
            live_pages = [p for p in self.context.pages if not p.is_closed()]
            if len(live_pages) <= 1:
                self._pages = live_pages
                return

            keeper = live_pages[0]
            for page in live_pages[1:]:
                try:
                    await page.close()
                except Exception:
                    pass

            self._pages = [keeper]

    def _handle_context_closed(self) -> None:
        self._pages.clear()
        self.context = None
        self._started = False
        self._closed_event.set()
