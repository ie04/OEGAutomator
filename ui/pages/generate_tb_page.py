import tkinter as tk
import threading
from tkinter import filedialog, messagebox, ttk

from ..widgets.action_button import ActionButton


class GenerateTBPage(tk.Frame):
    DEPENDENCY_OPTIONS = ("IND", "DEP")
    IND_OVERRIDE_OPTIONS = ("", "ACYR1", "ACYR2", "ACYR3", "ACYR4")

    def __init__(
        self,
        parent,
        controller,
        back_command=None,
        show_back_button=True,
        show_generate_button=True,
        success_callback=None,
    ):
        super().__init__(parent, bg="#C0C0C0")
        self.controller = controller
        self._back_command = back_command or self._default_back_command
        self._show_back_button = show_back_button
        self._show_generate_button = show_generate_button
        self._success_callback = success_callback

        self.start_date_var = tk.StringVar()
        self.program_code_var = tk.StringVar()
        self.sai_var = tk.StringVar()
        self.student_number_var = tk.StringVar()
        self.student_name_var = tk.StringVar()
        self.dep_ind_var = tk.StringVar(value=self.DEPENDENCY_OPTIONS[0])

        self.tas_var = tk.BooleanVar(value=False)
        self.ind_override_var = tk.StringVar(value=self.IND_OVERRIDE_OPTIONS[0])
        self.completer_program_code_var = tk.StringVar()
        self.nostaff_var = tk.BooleanVar(value=False)
        self.staff_used_ind_var = tk.StringVar()
        self.staff_used_dep_var = tk.StringVar()
        self.has_bs_var = tk.BooleanVar(value=False)
        self.crossover_sai_var = tk.StringVar()
        self.pell_used_var = tk.StringVar()
        self.file_var = tk.StringVar()
        self.outdir_var = tk.StringVar(value="out")
        self.optional_args_visible = False
        self._is_generating = False
        self._spinner_job = None
        self._spinner_phase = 0
        self._generation_result = None
        self._generation_error = None
        self._mousewheel_bound = False

        self._build()

    def _build(self):
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        title = tk.Label(
            self,
            text="Tuition Breakdown Generator",
            bg="#C0C0C0",
        )
        title.grid(row=0, column=0, pady=(20, 8), sticky="n")

        form_wrap = tk.Frame(self, bg="#C0C0C0")
        form_wrap.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 10))
        form_wrap.grid_rowconfigure(0, weight=1)
        form_wrap.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            form_wrap,
            bg="#C0C0C0",
            highlightthickness=0,
            bd=0,
            width=620,
            height=520,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        scrollbar = tk.Scrollbar(
            form_wrap,
            orient="vertical",
            command=self.canvas.yview,
        )
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(4, 0))
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.form = tk.Frame(self.canvas, bg="#C0C0C0")
        self._canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.form,
            anchor="nw",
        )

        self.form.bind("<Configure>", self._on_form_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.required_frame = tk.LabelFrame(
            self.form,
            text="Required Arguments",
            bg="#C0C0C0",
            padx=8,
            pady=8,
        )
        self.required_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.required_frame.grid_columnconfigure(0, weight=0, minsize=210)
        self.required_frame.grid_columnconfigure(1, weight=1, minsize=320)

        self.optional_toggle_button = ActionButton(
            self.form,
            text="Optional Arguments",
            icon=None,
            command=self._toggle_optional_arguments,
            width=220,
            height=32,
        )
        self.optional_toggle_button.grid(row=1, column=0, sticky="w", pady=(0, 10))

        self.optional_frame = tk.LabelFrame(
            self.form,
            text="Optional Arguments",
            bg="#C0C0C0",
            padx=8,
            pady=8,
        )
        self.optional_frame.grid(row=2, column=0, sticky="ew")
        self.optional_frame.grid_columnconfigure(0, weight=0, minsize=210)
        self.optional_frame.grid_columnconfigure(1, weight=1, minsize=320)
        self.optional_frame.grid_columnconfigure(2, weight=0)

        self.form.grid_columnconfigure(0, weight=1)

        self._build_required_fields()
        self._build_optional_fields()
        self.optional_frame.grid_remove()

        bottom = tk.Frame(self, bg="#C0C0C0")
        bottom.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=0)

        self.back_button = None
        if self._show_back_button:
            back_button = ActionButton(
                bottom,
                text="< Back",
                icon=None,
                command=self._go_back,
                width=120,
                height=32,
            )
            back_button.grid(row=0, column=0, sticky="w")
            self.back_button = back_button

        generate_wrap = tk.Frame(bottom, bg="#C0C0C0")
        generate_wrap.grid(row=0, column=1, sticky="e")
        generate_wrap.grid_columnconfigure(1, weight=0)

        self.loading_indicator = tk.Canvas(
            generate_wrap,
            width=18,
            height=18,
            bg="#C0C0C0",
            highlightthickness=0,
            bd=0,
        )
        self.loading_indicator.grid(row=0, column=0, padx=(0, 8), sticky="e")
        self.loading_indicator.grid_remove()

        self.generate_button = None
        if self._show_generate_button:
            self.generate_button = ActionButton(
                generate_wrap,
                text="Generate",
                icon=None,
                command=self._generate_tuition_breakdown,
                width=160,
                height=32,
            )
            self.generate_button.grid(row=0, column=1, sticky="e")

    def _build_required_fields(self):
        self.start_date_entry = self._add_entry(
            self.required_frame,
            0,
            "Start Date:",
            self.start_date_var,
        )
        self._add_entry(
            self.required_frame,
            1,
            "Program Code:",
            self.program_code_var,
        )
        self._add_entry(
            self.required_frame,
            2,
            "SAI:",
            self.sai_var,
        )
        self._add_entry(
            self.required_frame,
            3,
            "Student Number:",
            self.student_number_var,
        )
        self._add_entry(
            self.required_frame,
            4,
            "Student Name:",
            self.student_name_var,
        )
        self._add_dropdown(
            self.required_frame,
            5,
            "Dependency Type:",
            self.dep_ind_var,
            self.DEPENDENCY_OPTIONS,
        )

    def _build_optional_fields(self):
        self.boolean_flags_frame = tk.Frame(self.optional_frame, bg="#C0C0C0")
        self.boolean_flags_frame.grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(0, 8),
        )
        self._add_tiled_checkbox(self.boolean_flags_frame, 0, "TAS", self.tas_var)
        self._add_tiled_checkbox(
            self.boolean_flags_frame, 1, "No Staff", self.nostaff_var
        )
        self._add_tiled_checkbox(self.boolean_flags_frame, 2, "Has BS", self.has_bs_var)

        self._add_dropdown(
            self.optional_frame,
            1,
            "IND Override:",
            self.ind_override_var,
            self.IND_OVERRIDE_OPTIONS,
        )
        self._add_entry(
            self.optional_frame,
            2,
            "Completer Program Code:",
            self.completer_program_code_var,
        )
        self._add_entry(
            self.optional_frame,
            3,
            "Staff Used IND:",
            self.staff_used_ind_var,
        )
        self._add_entry(
            self.optional_frame,
            4,
            "Staff Used DEP:",
            self.staff_used_dep_var,
        )
        self._add_entry(
            self.optional_frame,
            5,
            "Crossover SAI:",
            self.crossover_sai_var,
        )
        self._add_entry(
            self.optional_frame,
            6,
            "Pell Used:",
            self.pell_used_var,
        )
        self._add_entry(
            self.optional_frame,
            7,
            "Template File:",
            self.file_var,
        )
        browse_template_button = ActionButton(
            self.optional_frame,
            text="Browse",
            icon=None,
            command=self._browse_template_file,
            width=100,
            height=28,
        )
        browse_template_button.grid(row=7, column=2, sticky="w", padx=(8, 0), pady=4)

        self._add_entry(
            self.optional_frame,
            8,
            "Output Directory:",
            self.outdir_var,
        )
        browse_outdir_button = ActionButton(
            self.optional_frame,
            text="Browse",
            icon=None,
            command=self._browse_output_directory,
            width=100,
            height=28,
        )
        browse_outdir_button.grid(row=8, column=2, sticky="w", padx=(8, 0), pady=4)

    def _add_label(self, parent, row, text):
        label = tk.Label(parent, text=text, bg="#C0C0C0", anchor="w")
        label.grid(row=row, column=0, sticky="w", pady=4)
        return label

    def _add_entry(self, parent, row, text, variable):
        self._add_label(parent, row, text)
        entry = tk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=4)
        return entry

    def _add_dropdown(self, parent, row, text, variable, values):
        self._add_label(parent, row, text)
        dropdown = ttk.Combobox(
            parent,
            textvariable=variable,
            values=values,
            state="readonly",
        )
        dropdown.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=4)
        return dropdown

    def _add_checkbox(self, parent, row, text, variable):
        checkbox = tk.Checkbutton(
            parent,
            text=text,
            variable=variable,
            bg="#C0C0C0",
            activebackground="#C0C0C0",
            selectcolor="#C0C0C0",
            anchor="w",
        )
        checkbox.grid(row=row, column=1, sticky="w", padx=(10, 0), pady=4)
        return checkbox

    def _add_tiled_checkbox(self, parent, column, text, variable):
        checkbox = tk.Checkbutton(
            parent,
            text=text,
            variable=variable,
            bg="#C0C0C0",
            activebackground="#C0C0C0",
            selectcolor="#C0C0C0",
            anchor="w",
        )
        checkbox.grid(row=0, column=column, sticky="w", padx=(0, 18), pady=2)
        return checkbox

    def _on_form_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self._canvas_window, width=event.width)

    def _bind_mousewheel(self):
        if self._mousewheel_bound:
            return

        root = self.winfo_toplevel()
        root.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        root.bind_all("<Button-4>", self._on_mousewheel, add="+")
        root.bind_all("<Button-5>", self._on_mousewheel, add="+")
        self._mousewheel_bound = True

    def _unbind_mousewheel(self):
        if not self._mousewheel_bound:
            return

        root = self.winfo_toplevel()
        root.unbind_all("<MouseWheel>")
        root.unbind_all("<Button-4>")
        root.unbind_all("<Button-5>")
        self._mousewheel_bound = False

    def _is_active_page(self):
        return self.winfo_ismapped() and self.winfo_viewable()

    def _on_mousewheel(self, event):
        if not self._is_active_page():
            return

        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
            return "break"

        if event.num == 5:
            self.canvas.yview_scroll(1, "units")
            return "break"

        delta = event.delta
        if delta == 0:
            return "break"

        steps = -max(1, abs(delta) // 120) if delta > 0 else max(1, abs(delta) // 120)
        self.canvas.yview_scroll(steps, "units")
        return "break"

    def _browse_template_file(self):
        selected_file = filedialog.askopenfilename(
            parent=self,
            title="Select Tuition Breakdown Template",
            filetypes=[
                ("Excel Macro-Enabled Workbook", "*.xlsm"),
                ("All Files", "*.*"),
            ],
        )
        if selected_file:
            self.file_var.set(selected_file)

    def _browse_output_directory(self):
        selected_directory = filedialog.askdirectory(
            parent=self,
            title="Select Output Directory",
        )
        if selected_directory:
            self.outdir_var.set(selected_directory)

    def _toggle_optional_arguments(self):
        self.optional_args_visible = not self.optional_args_visible
        if self.optional_args_visible:
            self.optional_frame.grid()
        else:
            self.optional_frame.grid_remove()
        self.after_idle(self._on_form_configure)

    def _generate_tuition_breakdown(self):
        if self._is_generating:
            return

        self._is_generating = True
        self._generation_result = None
        self._generation_error = None
        if self.generate_button is not None:
            self.generate_button.set_state("disabled")
        if self.back_button is not None:
            self.back_button.set_state("disabled")
        self.loading_indicator.grid()
        self._spinner_phase = 0
        self._animate_spinner()
        self.update_idletasks()

        request = {
            "start_date": self.start_date_var.get(),
            "program_code": self.program_code_var.get(),
            "sai": self.sai_var.get(),
            "student_number": self.student_number_var.get(),
            "student_name": self.student_name_var.get(),
            "dep_ind": self.dep_ind_var.get(),
            "tas": self.tas_var.get(),
            "ind_override": self.ind_override_var.get(),
            "completer_program_code": self.completer_program_code_var.get(),
            "nostaff": self.nostaff_var.get(),
            "staff_used_ind": self.staff_used_ind_var.get(),
            "staff_used_dep": self.staff_used_dep_var.get(),
            "has_bs": self.has_bs_var.get(),
            "crossover_sai": self.crossover_sai_var.get(),
            "pell_used": self.pell_used_var.get(),
            "file": self.file_var.get(),
            "outdir": self.outdir_var.get(),
        }

        worker = threading.Thread(
            target=self._run_generation,
            args=(request,),
            daemon=True,
        )
        worker.start()
        self.after(100, self._check_generation_status)

    def _run_generation(self, request):
        try:
            self._generation_result = self.controller.generate_tuition_breakdown(
                **request
            )
        except Exception as exc:
            self._generation_error = exc

    def _check_generation_status(self):
        if self._generation_result is None and self._generation_error is None:
            self.after(100, self._check_generation_status)
            return

        result = self._generation_result
        error = self._generation_error
        self._generation_result = None
        self._generation_error = None
        self._stop_loading_state()

        if error is not None:
            messagebox.showerror("Generate Tuition Breakdown Failed", str(error))
            return

        if result.output_text:
            self.controller.show_tb_output(result.output_text)

        if self._success_callback is not None and self._success_callback(result):
            return

        success_message = "Tuition Breakdown Successfully Generated."
        if result.pdf_path is not None:
            success_message += "\n\nThe PDF was opened in Adobe Acrobat."
        messagebox.showinfo("Tuition Breakdown Generated", success_message)

    def _animate_spinner(self):
        if not self._is_generating:
            return

        self.loading_indicator.delete("all")
        center_x = 9
        center_y = 9
        radius = 7
        points = [
            (center_x, center_y - radius),
            (center_x + 5, center_y - 5),
            (center_x + radius, center_y),
            (center_x + 5, center_y + 5),
            (center_x, center_y + radius),
            (center_x - 5, center_y + 5),
            (center_x - radius, center_y),
            (center_x - 5, center_y - 5),
        ]
        colors = (
            "#202020",
            "#505050",
            "#787878",
            "#909090",
            "#A8A8A8",
            "#C0C0C0",
            "#D0D0D0",
            "#E0E0E0",
        )

        for index, (x, y) in enumerate(points):
            color = colors[(index - self._spinner_phase) % len(colors)]
            self.loading_indicator.create_oval(
                x - 1.5,
                y - 1.5,
                x + 1.5,
                y + 1.5,
                fill=color,
                outline=color,
            )

        self._spinner_phase = (self._spinner_phase + 1) % len(points)
        self._spinner_job = self.after(90, self._animate_spinner)

    def _stop_loading_state(self):
        self._is_generating = False
        if self._spinner_job is not None:
            self.after_cancel(self._spinner_job)
            self._spinner_job = None
        self.loading_indicator.delete("all")
        self.loading_indicator.grid_remove()
        if self.generate_button is not None:
            self.generate_button.set_state("normal")
        if self.back_button is not None:
            self.back_button.set_state("normal")

    def on_show(self, reset=True):
        self._bind_mousewheel()
        if reset:
            self.reset_form()

        self.canvas.yview_moveto(0)
        self.after_idle(self.start_date_entry.focus_set)

    def on_hide(self):
        self._unbind_mousewheel()

    def reset_form(self):
        self.start_date_var.set("")
        self.program_code_var.set("")
        self.sai_var.set("")
        self.student_number_var.set("")
        self.student_name_var.set("")
        self.dep_ind_var.set(self.DEPENDENCY_OPTIONS[0])

        self.tas_var.set(False)
        self.ind_override_var.set(self.IND_OVERRIDE_OPTIONS[0])
        self.completer_program_code_var.set("")
        self.nostaff_var.set(False)
        self.staff_used_ind_var.set("")
        self.staff_used_dep_var.set("")
        self.has_bs_var.set(False)
        self.crossover_sai_var.set("")
        self.pell_used_var.set("")
        self.file_var.set("")
        self.outdir_var.set("out")
        self.optional_args_visible = False
        self.optional_frame.grid_remove()
        self._stop_loading_state()

    def prefill_from_student(self, student):
        def fmt_date(value):
            return value.strftime("%m/%d/%Y") if value is not None else ""

        full_name = " ".join(
            part.strip() for part in (student.first_name or "", student.last_name or "") if part.strip()
        )

        self.start_date_var.set(fmt_date(student.program_start_date))
        self.program_code_var.set(student.enrollment_version_code or "")
        self.student_number_var.set(student.student_id or "")
        self.student_name_var.set(full_name)
        self.dep_ind_var.set("DEP" if student.is_dependent else "IND")

    def get_preferred_size(self):
        self.update_idletasks()
        form_width = max(self.form.winfo_reqwidth(), 620)
        form_height = max(self.winfo_reqheight(), 520)
        return form_width + 36, form_height + 24

    def _go_back(self):
        self.on_hide()
        self._back_command()

    def _default_back_command(self):
        self.controller.show_page("MainPage")
