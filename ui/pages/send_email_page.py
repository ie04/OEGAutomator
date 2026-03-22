import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from datetime import date

from ..widgets.action_button import ActionButton


class SendEmailPage(tk.Frame):
    TASK_OPTIONS = (
        "HST", "HMT", "GIPI", "EA", "BSD", "CC", "SEI", "TCD", "COLT",
        "TAS", "TRA", "LNC", "PO", "NBC", "CEA", "MAD", "AA",
    )

    EMAIL_TYPES = (
        "Missed Contact",
        "Task List",
        "Estimated Financial Aid Breakdown",
    )

    def __init__(
        self,
        parent,
        controller,
        back_command=None,
        show_back_button=True,
        show_generate_button=True,
    ):
        super().__init__(parent, bg="#C0C0C0")
        self.controller = controller
        self._back_command = back_command or self._go_back
        self._show_back_button = show_back_button
        self._show_generate_button = show_generate_button

        self.email_type_var = tk.StringVar(value=self.EMAIL_TYPES[0])
        self.first_name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.student_id_var = tk.StringVar()
        self.start_date_var = tk.StringVar()
        self.attachment_path_var = tk.StringVar(value="")
        self.task_vars = {
            task: tk.BooleanVar(value=False) for task in self.TASK_OPTIONS
        }

        self._build()

    def _build(self):
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        title = tk.Label(
            self,
            text="OEG Email Generator",
            bg="#C0C0C0",
        )
        title.grid(row=0, column=0, pady=(20, 8), sticky="n")

        form_wrap = tk.Frame(self, bg="#C0C0C0")
        form_wrap.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 10))
        form_wrap.grid_columnconfigure(0, weight=1)
        form_wrap.grid_rowconfigure(0, weight=1)

        self.form = tk.Frame(form_wrap, bg="#C0C0C0")
        self.form.grid(row=0, column=0, sticky="nw")
        self.form.grid_columnconfigure(0, weight=0, minsize=190)
        self.form.grid_columnconfigure(1, weight=1, minsize=280)

        self._build_common_fields()
        self._build_task_list_fields()
        self._build_financial_aid_fields()
        self._set_conditional_fields()

        bottom = tk.Frame(self, bg="#C0C0C0")
        bottom.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=0)

        if self._show_back_button:
            back_button = ActionButton(
                bottom,
                text="< Back",
                icon=None,
                command=self._back_command,
                width=120,
                height=32,
            )
            back_button.grid(row=0, column=0, sticky="w")

        if self._show_generate_button:
            generate_button = ActionButton(
                bottom,
                text="Generate E-mail",
                icon=None,
                command=self._generate_email,
                width=180,
                height=32,
            )
            generate_column = 1 if self._show_back_button else 1
            generate_button.grid(row=0, column=generate_column, sticky="e")

    def _build_common_fields(self):
        self._add_label(0, "Select E-mail type:")

        self.email_type_dropdown = ttk.Combobox(
            self.form,
            textvariable=self.email_type_var,
            values=self.EMAIL_TYPES,
            state="readonly",
            width=30,
        )
        self.email_type_dropdown.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=4)
        self.email_type_dropdown.bind(
            "<<ComboboxSelected>>",
            lambda _event: self._set_conditional_fields(),
        )

        self._add_label(1, "First Name:")
        first_name_validate = (self.register(self._validate_first_name), "%P")
        self.first_name_entry = tk.Entry(
            self.form,
            textvariable=self.first_name_var,
            validate="key",
            validatecommand=first_name_validate,
        )
        self.first_name_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=4)

        self._add_label(2, "E-mail:")
        self.email_entry = tk.Entry(
            self.form,
            textvariable=self.email_var,
        )
        self.email_entry.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=4)

    def _build_task_list_fields(self):
        row = 3
        self.task_student_id_label = self._add_label(row, "Student ID:")
        student_id_validate = (self.register(self._validate_student_id), "%P")
        self.task_student_id_entry = tk.Entry(
            self.form,
            textvariable=self.student_id_var,
            validate="key",
            validatecommand=student_id_validate,
        )
        self.task_student_id_entry.grid(
            row=row,
            column=1,
            sticky="ew",
            padx=(10, 0),
            pady=4,
        )

        row += 1
        self.task_select_label = self._add_label(row, "Select Tasks:")
        self.task_options_frame = tk.Frame(self.form, bg="#C0C0C0")
        self.task_options_frame.grid(
            row=row,
            column=1,
            sticky="w",
            padx=(10, 0),
            pady=4,
        )

        for index, task in enumerate(self.TASK_OPTIONS):
            option = tk.Checkbutton(
                self.task_options_frame,
                text=task,
                variable=self.task_vars[task],
                bg="#C0C0C0",
                activebackground="#C0C0C0",
                selectcolor="#C0C0C0",
                anchor="w",
            )
            option.grid(
                row=index // 4,
                column=index % 4,
                sticky="w",
                padx=(0, 12),
                pady=2,
            )

    def _build_financial_aid_fields(self):
        row = 3
        self.start_date_label = self._add_label(row, "Start Date:")
        start_date_validate = (self.register(self._validate_start_date), "%P")
        self.start_date_entry = tk.Entry(
            self.form,
            textvariable=self.start_date_var,
            validate="key",
            validatecommand=start_date_validate,
        )
        self.start_date_entry.grid(
            row=row,
            column=1,
            sticky="ew",
            padx=(10, 0),
            pady=4,
        )

        row += 1
        self.attach_label = self._add_label(row, "Attach Tuition Breakdown:")
        self.attach_button = ActionButton(
            self.form,
            text="Browse",
            icon=None,
            command=self._attach_tuition_breakdown,
            width=140,
            height=28,
        )
        self.attach_button.grid(
            row=row,
            column=1,
            sticky="w",
            padx=(10, 0),
            pady=4,
        )

        row += 1
        self.attach_file_label = tk.Label(
            self.form,
            text="",
            bg="#C0C0C0",
            anchor="w",
        )
        self.attach_file_label.grid(
            row=row,
            column=1,
            sticky="w",
            padx=(10, 0),
            pady=(0, 4),
        )

    def _add_label(self, row, text):
        label = tk.Label(self.form, text=text, bg="#C0C0C0", anchor="w")
        label.grid(row=row, column=0, sticky="w", pady=4)
        return label

    def _set_conditional_fields(self):
        email_type = self.email_type_var.get()
        show_task_list = email_type == "Task List"
        show_financial_aid = email_type == "Estimated Financial Aid Breakdown"

        self._toggle_task_list_fields(show_task_list)
        self._toggle_financial_aid_fields(show_financial_aid)
        self.after_idle(self._fit_window_to_content)

    def _toggle_task_list_fields(self, should_show):
        widgets = (
            self.task_student_id_label,
            self.task_student_id_entry,
            self.task_select_label,
            self.task_options_frame,
        )
        for widget in widgets:
            if should_show:
                widget.grid()
            else:
                widget.grid_remove()

    def _toggle_financial_aid_fields(self, should_show):
        widgets = (
            self.start_date_label,
            self.start_date_entry,
            self.attach_label,
            self.attach_button,
            self.attach_file_label,
        )
        for widget in widgets:
            if should_show:
                widget.grid()
            else:
                widget.grid_remove()

    def _fit_window_to_content(self):
        self.controller.refresh_current_page_layout()

    def get_preferred_window_size(self):
        default_width, default_height = self.controller.get_default_window_size()
        self.update_idletasks()

        req_w = self.winfo_reqwidth() + 24
        req_h = self.winfo_reqheight() + 24

        return max(default_width, req_w), max(default_height, req_h)

    def get_max_preferred_window_size(self):
        default_width, default_height = self.controller.get_default_window_size()
        original_type = self.email_type_var.get()

        sizes = []
        for email_type in self.EMAIL_TYPES:
            self.email_type_var.set(email_type)
            self._toggle_task_list_fields(email_type == "Task List")
            self._toggle_financial_aid_fields(
                email_type == "Estimated Financial Aid Breakdown"
            )
            self.update_idletasks()
            sizes.append((self.winfo_reqwidth() + 24, self.winfo_reqheight() + 24))

        self.email_type_var.set(original_type)
        self._set_conditional_fields()
        self.update_idletasks()

        width = max(size[0] for size in sizes)
        height = max(size[1] for size in sizes)
        return max(default_width, width), max(default_height, height)

    def _validate_first_name(self, value):
        return value == "" or value.isalpha()

    def _validate_student_id(self, value):
        return value.isdigit() and len(value) <= 10 or value == ""

    def _validate_start_date(self, value):
        if value == "":
            return True

        if len(value) > 5:
            return False

        for char in value:
            if not (char.isdigit() or char == "/"):
                return False

        return value.count("/") <= 1

    def on_show(self):
        self.email_type_var.set(self.EMAIL_TYPES[0])
        self.first_name_var.set("")
        self.email_var.set("")
        self.student_id_var.set("")
        self.start_date_var.set("")
        self.attachment_path_var.set("")
        self.attach_file_label.config(text="")
        for task_var in self.task_vars.values():
            task_var.set(False)

        self._set_conditional_fields()
        self.after_idle(self.first_name_entry.focus_set)

    def prefill_from_student(self, student):
        def fmt_start_date(value: date | None) -> str:
            return value.strftime("%m/%d") if isinstance(value, date) else ""

        self.first_name_var.set(student.first_name or "")
        self.email_var.set(student.email or "")
        self.student_id_var.set(student.student_id or "")
        self.start_date_var.set(fmt_start_date(student.program_start_date))

    def _attach_tuition_breakdown(self):
        selected_file = filedialog.askopenfilename(
            parent=self,
            title="Select Tuition Breakdown PDF",
            filetypes=[("PDF Files", "*.pdf")],
        )
        if not selected_file:
            return

        attachment_path = Path(selected_file)
        if attachment_path.suffix.lower() != ".pdf":
            messagebox.showerror("Invalid File", "Please select a PDF file.")
            return

        self.attachment_path_var.set(str(attachment_path))
        self.attach_file_label.config(text=attachment_path.name)

    def _generate_email(self):
        email_type = self.email_type_var.get()

        try:
            if email_type == "Missed Contact":
                self.controller.generate_missed_contact_email(
                    first_name=self.first_name_var.get(),
                    to_email=self.email_var.get(),
                )
            elif email_type == "Task List":
                selected_tasks = [
                    task for task, variable in self.task_vars.items() if variable.get()
                ]
                self.controller.generate_tasklist_email(
                    first_name=self.first_name_var.get(),
                    to_email=self.email_var.get(),
                    student_id=self.student_id_var.get(),
                    selected_tasks=selected_tasks,
                )
            elif email_type == "Estimated Financial Aid Breakdown":
                self.controller.generate_est_finaid_email(
                    first_name=self.first_name_var.get(),
                    to_email=self.email_var.get(),
                    start_date=self.start_date_var.get(),
                    attachment_path=self.attachment_path_var.get(),
                )
        except Exception as exc:
            messagebox.showerror("Generate E-mail Failed", str(exc))

    def _go_back(self):
        self.controller.show_page("MainPage")
