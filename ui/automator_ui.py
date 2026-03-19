import ctypes
import traceback
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import tkinter as tk
from pathlib import Path

from application.services.generate_tasklist_email_service import (
    GenerateTasklistEmailService,
    TaskListEmailRequest,
)
from application.services.generate_missed_contact_email_service import (
    GenerateMissedContactEmailService,
    MissedContactEmailRequest,
)
from application.services.generate_est_finaid_email_service import (
    EstFinAidEmailRequest,
    GenerateEstFinAidEmailService,
)
from application.services.generate_tution_breakdown_service import (
    GenerateTutionBreakdownService,
)
from .pages.main_page import MainPage
from .pages.generate_tb_page import GenerateTBPage
from .pages.load_student_by_id_page import LoadStudentByIDPage
from .pages.send_email_page import SendEmailPage

from typing import Any
from PIL import Image, ImageTk

from application.ports import StudentSnapshot
from application.ports import NSLDSSnapshot



class AutomatorUI(tk.Tk):
    def __init__(self, runner):
        super().__init__()

        self.runner = runner
        self.est_finaid_email_service = GenerateEstFinAidEmailService()
        self.missed_contact_email_service = GenerateMissedContactEmailService()
        self.tasklist_email_service = GenerateTasklistEmailService()
        self.tution_breakdown_service = GenerateTutionBreakdownService()
        self._pending_jobs: dict[str, dict[str, Any]] = {}

        self.tk.call("tk", "scaling", 1.0)

        self.title("OEG Automation Suite")
        self.geometry("600x420")
        self.resizable(True, True)
        self.minsize(600, 420)

        self.BASE_DIR = Path(__file__).resolve().parent
        self.ASSETS = self.BASE_DIR / "icons"

        self.icons = {}
        self._load_icons()

        self.option_add("*Font", ("W95FA", -24))
        self.configure(bg="#C0C0C0")

        self.container = tk.Frame(self, bg="#C0C0C0")
        self.container.pack(fill="both", expand=True)

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for Page in (MainPage, LoadStudentByIDPage, SendEmailPage, GenerateTBPage):
            page_name = Page.__name__
            frame = Page(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_page("MainPage")
        self.after(100, self._poll_runner)

    def _load_icons(self):
        icon_size = (64, 64)
        nslds_icon_size = (150,65)

        def load_icon(path, size=icon_size, keep_aspect=False):
            img = Image.open(path).convert("RGBA")
            if keep_aspect:
                img.thumbnail(size, Image.Resampling.LANCZOS)
            else:
                img = img.resize(size, Image.NEAREST)
            return ImageTk.PhotoImage(img, master=self)

        self.icons["load_id"] = load_icon(self.ASSETS / "load_student_by_id.png")
        self.icons["send_email"] = load_icon(self.ASSETS / "send_email.png")
        self.icons["tuition_breakdown"] = load_icon(
            self.ASSETS / "tuition-breakdown.png"
        )
        self.icons["nslds"] = load_icon(
            self.ASSETS / "nslds-logo.png",
            size=nslds_icon_size,
            keep_aspect=True,
        )

    def show_page(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show()

    def load_student_by_id(self, student_id: str, requester) -> str:
        student_id = student_id.strip()

        if not student_id:
            raise ValueError("Please enter a Student ID.")

        if not student_id.isdigit():
            raise ValueError("Student ID must be numeric.")

        if len(student_id) != 10:
            raise ValueError("Student ID must be exactly 10 digits long.")

        job_id = self.runner.submit_student_lookup(student_id)
        self._pending_jobs[job_id] = {
            "type": "student_lookup",
            "requester": requester,
        }
        return job_id

    def query_nslds(self, student: StudentSnapshot, requester) -> str:
        job_id = self.runner.submit_query_nslds(student)
        self._pending_jobs[job_id] = {
            "type": "query_nslds",
            "requester": requester,
        }
        return job_id

    def generate_tasklist_email(
        self,
        first_name: str,
        to_email: str,
        student_id: str,
        selected_tasks: list[str],
    ) -> None:
        self.tasklist_email_service.generate_email(
            TaskListEmailRequest(
                first_name=first_name,
                to_email=to_email,
                student_id=student_id,
                selected_tasks=tuple(selected_tasks),
            )
        )

    def generate_missed_contact_email(
        self,
        first_name: str,
        to_email: str,
    ) -> None:
        self.missed_contact_email_service.generate_email(
            MissedContactEmailRequest(
                first_name=first_name,
                to_email=to_email,
            )
        )

    def generate_est_finaid_email(
        self,
        first_name: str,
        to_email: str,
        start_date: str,
        attachment_path: str,
    ) -> None:
        self.est_finaid_email_service.generate_email(
            EstFinAidEmailRequest(
                first_name=first_name,
                to_email=to_email,
                start_date=start_date,
                attachment_path=attachment_path,
            )
        )

    def generate_tuition_breakdown(
        self,
        *,
        start_date: str,
        program_code: str,
        sai: str,
        student_number: str,
        student_name: str,
        dep_ind: str,
        tas: bool = False,
        ind_override: str | None = None,
        completer_program_code: str | None = None,
        nostaff: bool = False,
        staff_used_ind: str | None = None,
        staff_used_dep: str | None = None,
        has_bs: bool = False,
        crossover_sai: str | None = None,
        pell_used: str | None = None,
        file: str | None = None,
        outdir: str = "out",
    ):
        return self.tution_breakdown_service.generate_tuition_breakdown(
            start_date=start_date,
            program_code=program_code,
            sai=sai,
            student_number=student_number,
            student_name=student_name,
            dep_ind=dep_ind,
            tas=tas,
            ind_override=ind_override,
            completer_program_code=completer_program_code,
            nostaff=nostaff,
            staff_used_ind=staff_used_ind,
            staff_used_dep=staff_used_dep,
            has_bs=has_bs,
            crossover_sai=crossover_sai,
            pell_used=pell_used,
            file=file,
            outdir=outdir,
        )

    def _poll_runner(self):
        while True:
            result = self.runner.get_result_nowait()
            if result is None:
                break

            job = self._pending_jobs.pop(result.job_id, None)
            if job is None:
                continue

            requester = job["requester"]
            job_type = job["type"]

            try:
                if job_type == "student_lookup":
                    if result.status == "success":
                        if hasattr(requester, "on_student_loaded"):
                            requester.on_student_loaded(result.payload)
                    else:
                        if hasattr(requester, "on_student_lookup_error"):
                            requester.on_student_lookup_error(
                                result.error or "Unknown error"
                            )
                elif job_type == "query_nslds":
                    if result.status == "success":
                        if hasattr(requester, "on_nslds_queried"):
                            requester.on_nslds_queried(result.payload)
                    else:
                        if hasattr(requester, "on_nslds_query_error"):
                            requester.on_nslds_query_error(
                                result.error or "Unknown error"
                            )
            except Exception as e:
                traceback.print_exc()
                

        self.after(100, self._poll_runner)
