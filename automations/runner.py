from __future__ import annotations

import asyncio
import queue
import threading
import traceback
import uuid
from dataclasses import dataclass
from typing import Any, Optional

from automations.playwright.browser import BrowserSession
from .config.settings import get_settings
from automations.playwright.salesforce.salesforce_client import SalesforceClient
from automations.playwright.nslds.nslds_client import NSLDSClient
from application.services.student_lookup_service import StudentLookupService
from application.services.query_nslds_service import QueryNSLDSService
from application.ports import StudentSnapshot


@dataclass(slots=True)
class AutomationResult:
    job_id: str
    status: str  # "success" | "error"
    payload: Any = None
    error: Optional[str] = None
    traceback_text: Optional[str] = None


class AutomationRunner:
    """
    Runs async Playwright automation on one dedicated background thread.

    Current scope:
    - handles StudentLookupService and QueryNSLDSService
    - one persistent BrowserSession
    - one persistent SalesforceClient
    - one persistent NSLDSClient
    - one persistent StudentLookupService
    - one persistent QueryNSLDSService
    - one job at a time
    - Tkinter can poll result queue safely from main thread
    """

    def __init__(self) -> None:
        self.settings = get_settings()

        self._job_queue: queue.Queue[tuple[str, str, dict[str, Any]]] = queue.Queue()
        self._result_queue: queue.Queue[AutomationResult] = queue.Queue()

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._started = False
        self._lock = threading.Lock()

    # -------------------------
    # Public lifecycle
    # -------------------------

    def start(self) -> None:
        with self._lock:
            if self.is_running:
                return

            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._thread_main,
                name="AutomationRunnerThread",
                daemon=True,
            )
            self._thread.start()
            self._started = True

    def stop(self, timeout: float = 10.0) -> None:
        with self._lock:
            if not self._started:
                return

            self._stop_event.set()
            self._job_queue.put(("__shutdown__", "__shutdown__", {}))

            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=timeout)

            self._thread = None
            self._started = False

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # -------------------------
    # Public job API
    # -------------------------

    def submit_student_lookup(self, student_id: str) -> str:
        student_id = student_id.strip()
        if not student_id:
            raise ValueError("student_id cannot be empty")

        if not self.is_running:
            raise RuntimeError("AutomationRunner is not running. Call start() first.")

        job_id = str(uuid.uuid4())
        self._job_queue.put(
            (
                job_id,
                "student_lookup",
                {"student_id": student_id},
            )
        )
        return job_id

    def submit_query_nslds(self, student: StudentSnapshot) -> str:
        if not isinstance(student, StudentSnapshot):
            raise TypeError("student must be a StudentSnapshot")

        if not self.is_running:
            raise RuntimeError("AutomationRunner is not running. Call start() first.")

        job_id = str(uuid.uuid4())
        self._job_queue.put(
            (
                job_id,
                "query_nslds",
                {"student": student},
            )
        )
        return job_id

    def get_result_nowait(self) -> Optional[AutomationResult]:
        try:
            return self._result_queue.get_nowait()
        except queue.Empty:
            return None

    def get_result_blocking(
        self,
        timeout: Optional[float] = None,
    ) -> Optional[AutomationResult]:
        try:
            return self._result_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    # -------------------------
    # Background thread entry
    # -------------------------

    def _thread_main(self) -> None:
        asyncio.run(self._async_main())

    async def _async_main(self) -> None:
        browser_session: Optional[BrowserSession] = None
        salesforce_client: Optional[SalesforceClient] = None
        nslds_client: Optional[NSLDSClient] = None
        student_lookup_service: Optional[StudentLookupService] = None
        query_nslds_service: Optional[QueryNSLDSService] = None

        try:
            while not self._stop_event.is_set():
                try:
                    job_id, job_type, payload = self._job_queue.get(timeout=0.25)
                except queue.Empty:
                    await asyncio.sleep(0.05)
                    continue

                if job_type == "__shutdown__":
                    break

                try:
                    if job_type in {"student_lookup", "query_nslds"}:
                        if browser_session is None or browser_session.is_closed:
                            if browser_session is not None:
                                try:
                                    await browser_session.stop()
                                except Exception:
                                    pass

                            browser_session = BrowserSession(
                                user_data_dir=str(self.settings.browser.chrome_profile),
                                channel=self.settings.browser.chrome_channel,
                                headless=self.settings.browser.headless,
                            )
                            await browser_session.start()
                            salesforce_client = SalesforceClient(
                                sf_cfg=self.settings.salesforce,
                                session=browser_session,
                            )
                            nslds_client = NSLDSClient(
                                nslds_cfg=self.settings.nslds,
                                session=browser_session,
                            )
                            student_lookup_service = StudentLookupService(
                                salesforce_client
                            )
                            query_nslds_service = QueryNSLDSService(nslds_client)

                        if job_type == "student_lookup":
                            result = await self._handle_student_lookup(
                                service=student_lookup_service,
                                payload=payload,
                            )
                        else:
                            result = await self._handle_query_nslds(
                                service=query_nslds_service,
                                payload=payload,
                            )
                        self._result_queue.put(
                            AutomationResult(
                                job_id=job_id,
                                status="success",
                                payload=result,
                            )
                        )
                    else:
                        raise ValueError(f"Unsupported job type: {job_type}")

                except Exception as exc:
                    self._result_queue.put(
                        AutomationResult(
                            job_id=job_id,
                            status="error",
                            error=str(exc),
                            traceback_text=traceback.format_exc(),
                        )
                    )

        except Exception as exc:
            self._result_queue.put(
                AutomationResult(
                    job_id="__runner__",
                    status="error",
                    error=f"AutomationRunner failed to initialize: {exc}",
                    traceback_text=traceback.format_exc(),
                )
            )
        finally:
            if browser_session is not None:
                try:
                    await browser_session.stop()
                except Exception:
                    pass

    # -------------------------
    # Job handlers
    # -------------------------

    async def _handle_student_lookup(
        self,
        service: StudentLookupService,
        payload: dict[str, Any],
    ) -> Any:
        student_id = str(payload["student_id"]).strip()
        if not student_id:
            raise ValueError("student_id cannot be empty")

        return await service.load_student(student_id)

    async def _handle_query_nslds(
        self,
        service: QueryNSLDSService,
        payload: dict[str, Any],
    ) -> Any:
        student = payload["student"]
        if not isinstance(student, StudentSnapshot):
            raise TypeError("student must be a StudentSnapshot")

        return await service.query_nslds(student)
