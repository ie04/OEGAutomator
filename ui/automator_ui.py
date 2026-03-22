import ctypes
import traceback
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "FullSail.OEGAutomator"
    )
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
from .pages.tb_output_page import TBOutputPage
from .pages.load_student_by_id_page import LoadStudentByIDPage
from .pages.send_email_page import SendEmailPage
from .pages.salesforce_helpers_page import SalesforceHelpersPage

from typing import Any
from PIL import Image, ImageTk

from application.ports import StudentSnapshot
from application.ports import NSLDSSnapshot



class AutomatorUI(tk.Tk):
    DEFAULT_WINDOW_WIDTH = 600
    DEFAULT_WINDOW_HEIGHT = 420

    def __init__(self, runner):
        super().__init__()
        self.withdraw()

        self.runner = runner
        self.est_finaid_email_service = GenerateEstFinAidEmailService()
        self.missed_contact_email_service = GenerateMissedContactEmailService()
        self.tasklist_email_service = GenerateTasklistEmailService()
        self.tution_breakdown_service = GenerateTutionBreakdownService()
        self._pending_jobs: dict[str, dict[str, Any]] = {}

        self.tk.call("tk", "scaling", 1.0)

        self.title("OEG Automation Suite")
        self.geometry(
            f"{self.DEFAULT_WINDOW_WIDTH}x{self.DEFAULT_WINDOW_HEIGHT}"
        )
        self.resizable(True, True)
        self.minsize(self.DEFAULT_WINDOW_WIDTH, self.DEFAULT_WINDOW_HEIGHT)

        self.BASE_DIR = Path(__file__).resolve().parent
        self.ASSETS = self.BASE_DIR / "icons"

        self._set_app_icon()
        self.icons = {}
        self._load_icons()

        self.option_add("*Font", ("W95FA", -24))
        self.configure(bg="#C0C0C0")

        self.container = tk.Frame(self, bg="#C0C0C0")
        self.container.pack(fill="both", expand=True)

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self._tb_output_windows: list[TBOutputPage] = []
        self._current_page_name: str | None = None

        for Page in (
            MainPage,
            LoadStudentByIDPage,
            SendEmailPage,
            GenerateTBPage,
            SalesforceHelpersPage,
        ):
            page_name = Page.__name__
            frame = Page(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        stable_width, stable_height = self._get_stable_window_size()
        self.geometry(f"{stable_width}x{stable_height}")

        self.show_page("MainPage")
        self.update_idletasks()
        self.deiconify()
        self.after(100, self._poll_runner)

    def _set_app_icon(self):
        if self.tk.call("tk", "windowingsystem") != "win32":
            return

        ico_icon_path = self.ASSETS / "fullsail-logo.ico"
        if not ico_icon_path.exists():
            return

        try:
            self.iconbitmap(default=str(ico_icon_path))
        except Exception:
            pass

    def _load_icons(self):
        icon_size = (64, 64)
        salesforce_icon_size = (84,84)
        salesforce_header_icon_size = (256, 128)
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
        self.icons["salesforce_helpers"] = load_icon(
            self.ASSETS / "salesforce-logo.png",
            size=salesforce_icon_size,
            keep_aspect=True,
        )
        self.icons["salesforce_header"] = load_icon(
            self.ASSETS / "salesforce-logo.png",
            size=salesforce_header_icon_size,
            keep_aspect=True,
        )
        self.icons["batch_add_ea"] = load_icon(
            self.ASSETS / "batch-add-ea.png"
        )
        self.icons["nslds"] = load_icon(
            self.ASSETS / "nslds-logo.png",
            size=nslds_icon_size,
            keep_aspect=True,
        )

    def get_main_action_button_size(self):
        grid = 4
        button_specs = (
            ("Load Student by Student ID", self.icons["load_id"]),
            ("Send Email", self.icons["send_email"]),
            ("Generate Tuition Breakdown", self.icons["tuition_breakdown"]),
            ("Salesforce Helpers", self.icons["salesforce_helpers"]),
        )

        temp_frame = tk.Frame(self.container, bg="#C0C0C0")
        temp_buttons = []

        for row, (text, icon) in enumerate(button_specs):
            button = tk.Button(
                temp_frame,
                text=text,
                image=icon,
                compound="left",
            )
            button.grid(row=row, column=0)
            temp_buttons.append(button)

        temp_frame.update_idletasks()

        max_icon_w = max(icon.width() for _, icon in button_specs)
        btn_width = max(button.winfo_reqwidth() for button in temp_buttons)
        btn_width += max_icon_w + (grid * 12)
        btn_height = max(button.winfo_reqheight() for button in temp_buttons)

        temp_frame.destroy()
        return btn_width, btn_height

    def get_default_window_size(self):
        return self.DEFAULT_WINDOW_WIDTH, self.DEFAULT_WINDOW_HEIGHT

    def _get_preferred_window_size(self, frame):
        default_width, default_height = self.get_default_window_size()

        if hasattr(frame, "get_preferred_window_size"):
            width, height = frame.get_preferred_window_size()
        else:
            frame.update_idletasks()
            width = frame.winfo_reqwidth() + 24
            height = frame.winfo_reqheight() + 24

        return max(default_width, width), max(default_height, height)

    def _get_stable_window_size(self):
        default_width, default_height = self.get_default_window_size()
        max_width = default_width
        max_height = default_height

        for frame in self.frames.values():
            if hasattr(frame, "get_max_preferred_window_size"):
                width, height = frame.get_max_preferred_window_size()
            else:
                width, height = self._get_preferred_window_size(frame)

            max_width = max(max_width, width)
            max_height = max(max_height, height)

        return max_width, max_height

    def _apply_window_layout(self, frame):
        self.update_idletasks()
        _ = frame

    def show_page(self, page_name):
        frame = self.frames[page_name]
        previous_page = (
            self.frames[self._current_page_name]
            if self._current_page_name is not None
            else None
        )

        if previous_page is not None and previous_page is not frame:
            if hasattr(previous_page, "on_hide"):
                previous_page.on_hide()

        if hasattr(frame, "on_show"):
            frame.on_show()
        self._apply_window_layout(frame)
        frame.tkraise()
        self._current_page_name = page_name

    def refresh_current_page_layout(self):
        if self._current_page_name is None:
            return

        frame = self.frames[self._current_page_name]
        self._apply_window_layout(frame)

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

    def batch_add_ea(self, student_ids: list[str], requester) -> str:
        job_id = self.runner.submit_batch_add_ea(student_ids)
        self._pending_jobs[job_id] = {
            "type": "batch_add_ea",
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

    def show_tb_output(self, output_text: str) -> None:
        output_window = TBOutputPage(self, output_text=output_text)
        self._tb_output_windows.append(output_window)

        def _cleanup():
            try:
                self._tb_output_windows.remove(output_window)
            except ValueError:
                pass
            output_window.destroy()

        output_window.protocol("WM_DELETE_WINDOW", _cleanup)

    def _poll_runner(self):
        while True:
            result = self.runner.get_result_nowait()
            if result is None:
                break

            if result.status == "progress":
                job = self._pending_jobs.get(result.job_id)
            else:
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
                elif job_type == "batch_add_ea":
                    if result.status == "progress":
                        if hasattr(requester, "on_batch_add_ea_progress"):
                            requester.on_batch_add_ea_progress(str(result.payload))
                    elif result.status == "success":
                        if hasattr(requester, "on_batch_add_ea_completed"):
                            requester.on_batch_add_ea_completed(result.payload)
                    else:
                        if hasattr(requester, "on_batch_add_ea_error"):
                            requester.on_batch_add_ea_error(
                                result.error or "Unknown error"
                            )
            except Exception as e:
                traceback.print_exc()
                

        self.after(100, self._poll_runner)
