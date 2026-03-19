from application.ports import NSLDSPort, NSLDSSnapshot
from ..browser import BrowserSession
from ...config.settings import NSLDSSettings
from .pages.auth import AuthFlow
from .pages.pull_up_student import PullUpStudent
from .pages.aid_page import AidPage
from  .pages.enrollment_page import EnrollmentPage

class NSLDSClient(NSLDSPort):
    def __init__(self, nslds_cfg: NSLDSSettings, session: BrowserSession):
        self.cfg = nslds_cfg
        self.session = session

    async def fetch_NSLDS_snapshot(self, student) -> NSLDSSnapshot:
        page = await self.session.new_page()    


        url = str(self.cfg.base_url)
        await page.goto(url)

        await page.wait_for_url(
            lambda url: url.rstrip("/") in {
                "https://nsldsfap.ed.gov/login",
                "https://nsldsfap.ed.gov/home",
            },
            wait_until="load",
        )

        current_url = page.url.rstrip("/")

        if current_url == "https://nsldsfap.ed.gov/login":
            await AuthFlow(page).login(self.cfg.username, self.cfg.password)
        elif current_url == "https://nsldsfap.ed.gov/home":
            nslds_snapshot = await PullUpStudent(page).search(student)
        
        if nslds_snapshot is not None:
            await AidPage(page).scrape_aid_page(nslds_snapshot)
            await EnrollmentPage(page).scrape_enrollment_page(nslds_snapshot)


            return nslds_snapshot

