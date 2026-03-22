import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import messagebox
from datetime import date
from application.ports import StudentSnapshot
from ..widgets.action_button import ActionButton
from .send_email_page import SendEmailPage
from .generate_tb_page import GenerateTBPage


class LoadStudentByIDPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#C0C0C0")
        self.controller = controller
        self.student_id_var = tk.StringVar()
        self._is_loading = False
        self._loaded_student = None
        self._nslds_snapshot = None
        self._is_querying_nslds = False
        self._right_panel_mode = "buttons"
        self._tb_prefill_student_id = None
        self._build()

    def _build(self):
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        top = tk.Frame(self, bg="#C0C0C0")
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        top.grid_columnconfigure(1, weight=1)

        tk.Label(top, text="Enter Student ID:", bg="#C0C0C0").grid(
            row=0, column=0, sticky="w"
        )

        self.IDEntryTextInput = tk.Entry(
            top,
            textvariable=self.student_id_var,
            name="identrytextinput",
        )
        self.IDEntryTextInput.grid(row=0, column=1, sticky="ew", padx=(10, 10))
        self.IDEntryTextInput.bind("<Return>", lambda e: self._submit())

        self.load_btn = ActionButton(
            top,
            text="Load",
            icon=None,
            command=self._submit,
            width=90,
            height=28,
        )
        self.load_btn.grid(row=0, column=2, sticky="e")

        content = tk.Frame(self, bg="#C0C0C0")
        content.grid(row=1, column=0, sticky="nsew", padx=12, pady=(6, 10))
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)

        self.info = StudentInfoDisplay(content)
        self.info.grid(row=0, column=0, sticky="nsew")
        self.info.clear()

        self.action_panel = tk.Frame(content, bg="#C0C0C0")
        self.action_panel.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        self.action_panel.grid_rowconfigure(0, weight=1)
        self.action_panel.grid_columnconfigure(0, weight=1)

        self.button_stack = tk.Frame(self.action_panel, bg="#C0C0C0")
        self.button_stack.grid(row=0, column=0, sticky="n")

        email_btn_width, email_btn_height = self._get_main_page_button_size(self.button_stack)
        self.send_email_btn = ActionButton(
            self.button_stack,
            text="Send Email",
            icon=self.controller.icons["send_email"],
            command=self._open_send_email_page,
            width=email_btn_width,
            height=email_btn_height,
            state="disabled",
        )
        self.send_email_btn.grid(row=0, column=0, sticky="n")

        self.query_nslds_btn = ActionButton(
            self.button_stack,
            text="Query NSLDS",
            icon=self.controller.icons["nslds"],
            command=self._query_nslds,
            width=email_btn_width,
            height=email_btn_height,
            state="disabled",
        )
        self.query_nslds_btn.grid(row=1, column=0, sticky="n", pady=(8, 0))

        self.tb_button = ActionButton(
            self.button_stack,
            text="Generate Tuition Breakdown",
            icon=self.controller.icons["tuition_breakdown"],
            command=self._open_generate_tb_page,
            width=email_btn_width,
            height=email_btn_height,
            state="disabled",
        )
        self.tb_button.grid(row=2, column=0, sticky="n", pady=(8, 0))

        self.embedded_send_email_page = SendEmailPage(
            parent=self.action_panel,
            controller=self.controller,
            back_command=self._hide_send_email_page,
            show_back_button=False,
            show_generate_button=False,
        )
        self.embedded_send_email_page.grid(row=0, column=0, sticky="nsew")
        self.embedded_send_email_page.grid_remove()

        self.embedded_tb_page = GenerateTBPage(
            parent=self.action_panel,
            controller=self.controller,
            back_command=self._hide_generate_tb_page,
            show_back_button=False,
            show_generate_button=False,
            success_callback=self._on_embedded_tb_generated,
        )
        self.embedded_tb_page.grid(row=0, column=0, sticky="nsew")
        self.embedded_tb_page.grid_remove()

        bottom = tk.Frame(self, bg="#C0C0C0")
        bottom.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=0)

        self.back_btn = ActionButton(
            bottom,
            text="← Back",
            icon=None,
            command=self._go_back,
            width=120,
            height=32,
        )
        self.back_btn.grid(row=0, column=0, sticky="w")

        self.generate_email_btn = ActionButton(
            bottom,
            text="Generate E-mail",
            icon=None,
            command=self._generate_embedded_email,
            width=180,
            height=32,
        )
        self.generate_email_btn.grid(row=0, column=1, sticky="e")
        self.generate_email_btn.grid_remove()

        self.generate_tb_btn = ActionButton(
            bottom,
            text="Generate",
            icon=None,
            command=self._generate_embedded_tb,
            width=180,
            height=32,
        )
        self.generate_tb_btn.grid(row=0, column=1, sticky="e")
        self.generate_tb_btn.grid_remove()

    def _get_main_page_button_size(self, parent):
        grid_unit = 4
        tmp_load = tk.Button(
            parent,
            text="Load Student by Student ID",
            image=self.controller.icons["load_id"],
            compound="left",
        )
        tmp_email = tk.Button(
            parent,
            text="Send Email",
            image=self.controller.icons["send_email"],
            compound="left",
        )
        tmp_nslds = tk.Button(
            parent,
            text="Query NSLDS",
            image=self.controller.icons["nslds"],
            compound="left",
        )
        tmp_tb = tk.Button(
            parent,
            text="Generate Tuition Breakdown",
            image=self.controller.icons["tuition_breakdown"],
            compound="left",
        )

        tmp_load.grid(row=0, column=0)
        tmp_email.grid(row=1, column=0)
        tmp_nslds.grid(row=2, column=0)
        tmp_tb.grid(row=3, column=0)
        self.update_idletasks()

        max_icon_w = max(
            self.controller.icons["load_id"].width(),
            self.controller.icons["send_email"].width(),
            self.controller.icons["nslds"].width(),
            self.controller.icons["tuition_breakdown"].width(),
        )
        btn_width = max(
            tmp_load.winfo_reqwidth(),
            tmp_email.winfo_reqwidth(),
            tmp_nslds.winfo_reqwidth(),
            tmp_tb.winfo_reqwidth(),
        ) + max_icon_w + (grid_unit * 8)
        btn_height = max(
            tmp_load.winfo_reqheight(),
            tmp_email.winfo_reqheight(),
            tmp_nslds.winfo_reqheight(),
            tmp_tb.winfo_reqheight(),
        )

        tmp_load.destroy()
        tmp_email.destroy()
        tmp_nslds.destroy()
        tmp_tb.destroy()

        return btn_width, btn_height

    def _fit_window_to_content(self):
        self.controller.refresh_current_page_layout()

    def get_preferred_window_size(self):
        default_width, default_height = self.controller.get_default_window_size()

        self.update_idletasks()
        req_w = self.winfo_reqwidth() + 48
        req_h = self.winfo_reqheight() + 40

        if self._right_panel_mode == "tb":
            tb_width, tb_height = self.embedded_tb_page.get_preferred_size()
            info_width = self.info.winfo_reqwidth()
            top_width = self.winfo_children()[0].winfo_reqwidth() if self.winfo_children() else 0
            bottom_width = self.winfo_children()[2].winfo_reqwidth() if len(self.winfo_children()) > 2 else 0
            req_w = max(
                req_w,
                info_width + tb_width + 96,
                top_width + 32,
                bottom_width + 32,
            )
            req_h = max(req_h, tb_height + 160)

        return max(default_width, req_w), max(default_height, req_h)

    def get_max_preferred_window_size(self):
        default_width, default_height = self.controller.get_default_window_size()

        self.update_idletasks()
        req_w = self.winfo_reqwidth() + 48
        req_h = self.winfo_reqheight() + 40

        tb_width, tb_height = self.embedded_tb_page.get_preferred_size()
        info_width = self.info.winfo_reqwidth()
        top_width = self.winfo_children()[0].winfo_reqwidth() if self.winfo_children() else 0
        bottom_width = self.winfo_children()[2].winfo_reqwidth() if len(self.winfo_children()) > 2 else 0
        req_w = max(
            req_w,
            info_width + tb_width + 96,
            top_width + 32,
            bottom_width + 32,
        )
        req_h = max(req_h, tb_height + 160)

        return max(default_width, req_w), max(default_height, req_h)

    def _set_loading_state(self, is_loading: bool):
        self._is_loading = is_loading
        self.IDEntryTextInput.config(state="disabled" if is_loading else "normal")
        if is_loading:
            self.send_email_btn.set_state("disabled")
            self.query_nslds_btn.set_state("disabled")
            self.tb_button.set_state("disabled")

    def on_show(self):
        self.student_id_var.set("")
        self._loaded_student = None
        self._nslds_snapshot = None
        self._is_querying_nslds = False
        self._tb_prefill_student_id = None
        self._right_panel_mode = "buttons"
        self.info.clear()
        self._set_loading_state(False)
        self._hide_send_email_page()
        self._hide_generate_tb_page(reset=True)
        self.send_email_btn.set_state("disabled")
        self.query_nslds_btn.set_state("disabled")
        self.tb_button.set_state("disabled")
        self.generate_email_btn.grid_remove()
        self.generate_tb_btn.grid_remove()
        self.after_idle(self.IDEntryTextInput.focus_set)

    def _go_back(self):
        if self._is_loading:
            return
        if self._right_panel_mode == "email":
            self._hide_send_email_page()
            self.after(0, self._fit_window_to_content)
            return
        if self._right_panel_mode == "tb_email":
            self._hide_send_email_page(return_to="tb")
            self.after(0, self._fit_window_to_content)
            return
        if self._right_panel_mode == "tb":
            self._hide_generate_tb_page()
            self.after(0, self._fit_window_to_content)
            return
        self.student_id_var.set("")
        self._loaded_student = None
        self._nslds_snapshot = None
        self._is_querying_nslds = False
        self._tb_prefill_student_id = None
        self.info.clear()
        self._hide_send_email_page()
        self._hide_generate_tb_page(reset=True)
        self.send_email_btn.set_state("disabled")
        self.query_nslds_btn.set_state("disabled")
        self.tb_button.set_state("disabled")
        self.controller.show_page("MainPage")

    def _submit(self):
        if self._is_loading:
            return

        student_id = self.student_id_var.get().strip()
        self._loaded_student = None
        self._nslds_snapshot = None
        self._is_querying_nslds = False
        self._tb_prefill_student_id = None
        self.info.clear()
        self._hide_send_email_page()
        self._hide_generate_tb_page(reset=True)

        if not student_id:
            messagebox.showwarning("Missing Student ID", "Please enter a Student ID.")
            return

        try:
            self._set_loading_state(True)
            self.controller.load_student_by_id(student_id, requester=self)
        except Exception as e:
            self._set_loading_state(False)
            messagebox.showerror("Lookup Failed", str(e))
            self.student_id_var.set("")
            self.IDEntryTextInput.focus_set()
            self.after(0, self._fit_window_to_content)

    def on_student_loaded(self, student: StudentSnapshot):
        self._set_loading_state(False)
        self._loaded_student = student
        self._nslds_snapshot = None
        self._is_querying_nslds = False
        self._tb_prefill_student_id = None
        self.info.set_student(student)
        self.send_email_btn.set_state("normal")
        self.query_nslds_btn.set_state("normal")
        self.tb_button.set_state("normal")
        self.after(0, self._fit_window_to_content)

    def on_student_lookup_error(self, message: str):
        self._set_loading_state(False)
        self.student_id_var.set("")
        self._loaded_student = None
        self._nslds_snapshot = None
        self._is_querying_nslds = False
        self._tb_prefill_student_id = None
        self.info.clear()
        self._hide_send_email_page()
        self._hide_generate_tb_page(reset=True)
        self.send_email_btn.set_state("disabled")
        self.query_nslds_btn.set_state("disabled")
        self.tb_button.set_state("disabled")
        self.IDEntryTextInput.config(state="normal")
        self.IDEntryTextInput.focus_set()
        messagebox.showerror("Lookup Failed", message)
        self.after(0, self._fit_window_to_content)

    def _open_send_email_page(self):
        if self._loaded_student is None:
            return

        self.embedded_send_email_page.on_show()
        self.embedded_send_email_page.prefill_from_student(self._loaded_student)
        self.button_stack.grid_remove()
        self.embedded_send_email_page.grid()
        self.generate_email_btn.grid()
        self._right_panel_mode = "email"
        self.embedded_send_email_page.first_name_entry.focus_set()
        self.after(0, self._fit_window_to_content)

    def _hide_send_email_page(self, return_to="buttons"):
        self.embedded_send_email_page.email_type_var.set(
            self.embedded_send_email_page.EMAIL_TYPES[0]
        )
        self.embedded_send_email_page._set_conditional_fields()
        self.embedded_send_email_page.grid_remove()
        self.generate_email_btn.grid_remove()
        if return_to == "tb":
            self.embedded_tb_page.grid()
            self.generate_tb_btn.grid()
            self._right_panel_mode = "tb"
        else:
            self.button_stack.grid()
            self._right_panel_mode = "buttons"

    def _open_generate_tb_page(self):
        if self._loaded_student is None:
            return

        current_student_id = self._loaded_student.student_id or ""
        if self._tb_prefill_student_id != current_student_id:
            self.embedded_tb_page.on_show(reset=True)
            self.embedded_tb_page.prefill_from_student(self._loaded_student)
            self._tb_prefill_student_id = current_student_id
        else:
            self.embedded_tb_page.on_show(reset=False)

        self.button_stack.grid_remove()
        self.embedded_tb_page.grid()
        self.generate_tb_btn.grid()
        self._right_panel_mode = "tb"
        self.embedded_tb_page.start_date_entry.focus_set()
        self.after(0, self._fit_window_to_content)

    def _hide_generate_tb_page(self, reset=False):
        self.embedded_tb_page.on_hide()
        self.embedded_tb_page.grid_remove()
        self.generate_tb_btn.grid_remove()
        self.button_stack.grid()
        if reset:
            self.embedded_tb_page.reset_form()
            self._tb_prefill_student_id = None
        self._right_panel_mode = "buttons"

    def _generate_embedded_email(self):
        self.embedded_send_email_page._generate_email()

    def _generate_embedded_tb(self):
        self.embedded_tb_page._generate_tuition_breakdown()

    def _on_embedded_tb_generated(self, result):
        should_attach = messagebox.askyesno(
            "Tuition Breakdown Generated",
            "Tuition Breakdown Succesfully Generated. Attach to E-mail?",
        )
        if not should_attach:
            return False

        if self._loaded_student is None or result.pdf_path is None:
            return False

        self.embedded_tb_page.grid_remove()
        self.generate_tb_btn.grid_remove()

        self.embedded_send_email_page.on_show()
        self.embedded_send_email_page.prefill_from_student(self._loaded_student)
        self.embedded_send_email_page.email_type_var.set(
            "Estimated Financial Aid Breakdown"
        )
        self.embedded_send_email_page.attachment_path_var.set(str(result.pdf_path))
        self.embedded_send_email_page.attach_file_label.config(
            text=Path(result.pdf_path).name
        )
        self.embedded_send_email_page._set_conditional_fields()
        self.embedded_send_email_page.grid()
        self.generate_email_btn.grid()
        self._right_panel_mode = "tb_email"
        self.embedded_send_email_page.first_name_entry.focus_set()
        self.after(0, self._fit_window_to_content)
        return True

    def _query_nslds(self):
        if self._loaded_student is None or self._is_querying_nslds:
            return

        self._is_querying_nslds = True
        self.query_nslds_btn.set_state("disabled")
        self.controller.query_nslds(self._loaded_student, requester=self)

    def on_nslds_queried(self, snapshot):
        self._nslds_snapshot = snapshot
        self._is_querying_nslds = False
        if self._loaded_student is not None:
            self.query_nslds_btn.set_state("normal")

    def on_nslds_query_error(self, message: str):
        self._is_querying_nslds = False
        if self._loaded_student is not None:
            self.query_nslds_btn.set_state("normal")
        messagebox.showerror("NSLDS Query Failed", message)


class StudentInfoDisplay(tk.LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, text="Student Info", bg="#C0C0C0")

        self._vars = {
            "student_id": tk.StringVar(value=""),
            "first_name": tk.StringVar(value=""),
            "last_name": tk.StringVar(value=""),
            "dob": tk.StringVar(value=""),
            "ssn": tk.StringVar(value=""),
            "enrollment_version_code": tk.StringVar(value=""),
            "program_start_date": tk.StringVar(value=""),
            "is_dependent": tk.StringVar(value=""),
            "email": tk.StringVar(value=""),
        }

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1, minsize=self._value_column_minsize())

        label_overrides = {
            "student_id": "Student ID:",
            "dob": "DOB:",
            "ssn": "SSN:"
            
        }

        for r, (k, v) in enumerate(self._vars.items()):
            label = label_overrides.get(k, k.replace("_", " ").title() + ":")
            tk.Label(self, text=label, bg="#C0C0C0", anchor="w").grid(
                row=r, column=0, sticky="w", padx=8, pady=2
            )
            tk.Label(self, textvariable=v, bg="#C0C0C0", anchor="w").grid(
                row=r, column=1, sticky="ew", padx=8, pady=2
            )

    def _value_column_minsize(self) -> int:
        font = tkfont.nametofont("TkDefaultFont")
        samples = (
            "0000000000",
            "Alexandria",
            "Montgomery-Washington",
            "12/31/2026",
            "000-00-0000",
            "GDVAS01-ONLINE",
            "studentemailaddress@example.com",
            "Yes",
        )
        return max(font.measure(sample) for sample in samples) + 24

    def clear(self):
        for v in self._vars.values():
            v.set("")

    def set_student(self, student: StudentSnapshot) -> None:
        def fmt_date(value: date | None) -> str:
            return value.strftime("%m/%d/%Y") if isinstance(value, date) else ""

        def fmt_ssn(value: str | None) -> str:
            if not value:
                return ""

            digits = "".join(ch for ch in str(value) if ch.isdigit())
            if len(digits) != 9:
                return str(value)

            return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"

        self._vars["student_id"].set(student.student_id or "")
        self._vars["first_name"].set(student.first_name or "")
        self._vars["last_name"].set(student.last_name or "")
        self._vars["dob"].set(fmt_date(student.dob))
        self._vars["ssn"].set(fmt_ssn(student.ssn))
        self._vars["enrollment_version_code"].set(student.enrollment_version_code or "")
        self._vars["program_start_date"].set(fmt_date(student.program_start_date))
        self._vars["is_dependent"].set("Yes" if student.is_dependent else "No")
        self._vars["email"].set(student.email or "")
