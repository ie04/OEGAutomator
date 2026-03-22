import re
import tkinter as tk

from ..widgets.action_button import ActionButton


class SalesforceHelpersPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#C0C0C0")
        self.controller = controller
        self._mode = "menu"
        self._current_job_id: str | None = None
        self._build()

    def _build(self):
        grid = 4

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        title = tk.Label(
            self,
            image=self.controller.icons["salesforce_header"],
            bg="#C0C0C0",
        )
        title.grid(row=0, column=0, pady=(grid * 4, 0), sticky="n")

        body = tk.Frame(self, bg="#C0C0C0")
        body.grid(row=1, column=0, sticky="nsew", padx=12, pady=(8, 8))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)

        self.content = tk.Frame(body, bg="#C0C0C0")
        self.content.grid(row=0, column=0, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self._build_menu()
        self._build_batch_workspace()

        bottom = tk.Frame(self, bg="#C0C0C0")
        bottom.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=0)

        self.back_btn = ActionButton(
            bottom,
            text="< Back",
            icon=None,
            command=self._go_back,
            width=120,
            height=32,
        )
        self.back_btn.grid(row=0, column=0, sticky="w")

        self.action_btn = ActionButton(
            bottom,
            text="Run",
            icon=None,
            command=self._run_batch_add_ea,
            width=160,
            height=32,
        )
        self.action_btn.grid(row=0, column=1, sticky="e")
        self.action_btn.grid_remove()

        self._show_menu()

    def _build_menu(self):
        grid = 4
        self.menu_frame = tk.Frame(self.content, bg="#C0C0C0")
        self.menu_frame.grid_rowconfigure(0, weight=1)
        self.menu_frame.grid_rowconfigure(1, weight=0)
        self.menu_frame.grid_rowconfigure(2, weight=1)
        self.menu_frame.grid_columnconfigure(0, weight=1)

        btn_wrap = tk.Frame(self.menu_frame, bg="#C0C0C0")
        btn_wrap.grid(row=1, column=0)

        btn_width, btn_height = self._get_batch_add_ea_button_size(btn_wrap)

        self.batch_add_ea_btn = ActionButton(
            btn_wrap,
            text="Batch Add Enrollment Agreements",
            icon=self.controller.icons["batch_add_ea"],
            command=self._open_batch_add_ea,
            width=btn_width,
            height=btn_height,
        )
        self.batch_add_ea_btn.grid(row=0, column=0, pady=grid)

    def _build_batch_workspace(self):
        self.batch_frame = tk.Frame(self.content, bg="#C0C0C0")
        self.batch_frame.grid_rowconfigure(0, weight=0)
        self.batch_frame.grid_rowconfigure(1, weight=1)
        self.batch_frame.grid_columnconfigure(0, weight=1)

        self.batch_prompt = tk.Label(
            self.batch_frame,
            text="Enter Student IDs separated by newlines, spaces, or commas:",
            bg="#C0C0C0",
            anchor="w",
            justify="left",
        )
        self.batch_prompt.grid(row=0, column=0, sticky="w", pady=(0, 8))

        text_wrap = tk.Frame(self.batch_frame, bg="#C0C0C0")
        text_wrap.grid(row=1, column=0, sticky="nsew")
        text_wrap.grid_rowconfigure(0, weight=1)
        text_wrap.grid_columnconfigure(0, weight=1)

        self.batch_text = tk.Text(
            text_wrap,
            wrap="word",
            width=60,
            height=16,
            undo=True,
        )
        self.batch_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(
            text_wrap,
            orient="vertical",
            command=self.batch_text.yview,
        )
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(8, 0))
        self.batch_text.configure(yscrollcommand=scrollbar.set)

    def on_show(self):
        if self._mode == "menu":
            self.after_idle(self.batch_add_ea_btn.focus_set)
        else:
            self.after_idle(self.batch_text.focus_set)

    def _open_batch_add_ea(self):
        self._show_batch_input(clear_text=True)

    def _show_menu(self):
        self._mode = "menu"
        self.menu_frame.grid(row=0, column=0, sticky="nsew")
        self.batch_frame.grid_remove()
        self.action_btn.grid_remove()
        self._set_back_button_enabled(True)

    def _show_batch_input(self, clear_text: bool):
        self._mode = "input"
        self.menu_frame.grid_remove()
        self.batch_frame.grid(row=0, column=0, sticky="nsew")
        self.batch_prompt.config(
            text="Enter Student IDs separated by newlines, spaces, or commas:"
        )
        self.batch_text.configure(state="normal")
        if clear_text:
            self.batch_text.delete("1.0", "end")
        self.action_btn.grid()
        self._set_action_button(
            text="Run",
            command=self._run_batch_add_ea,
            enabled=True,
            depressed=False,
        )
        self._set_back_button_enabled(True)
        self.after_idle(self.batch_text.focus_set)

    def _show_batch_output(self):
        self._mode = "running"
        self.menu_frame.grid_remove()
        self.batch_frame.grid(row=0, column=0, sticky="nsew")
        self.batch_prompt.config(text="Batch Add Enrollment Agreements Output:")
        self.batch_text.configure(state="normal")
        self.batch_text.delete("1.0", "end")
        self.batch_text.configure(state="disabled")
        self.action_btn.grid()
        self._set_action_button(
            text="Run",
            command=self._run_batch_add_ea,
            enabled=False,
            depressed=True,
        )
        self._set_back_button_enabled(False)

    def _show_batch_done(self):
        self._mode = "done"
        self._set_action_button(
            text="Done",
            command=self._reset_batch_workspace,
            enabled=True,
            depressed=False,
        )
        self._set_back_button_enabled(True)

    def _reset_batch_workspace(self):
        self._current_job_id = None
        self._show_batch_input(clear_text=True)

    def _go_back(self):
        if self._mode == "menu":
            self.controller.show_page("MainPage")
            return

        if self._mode == "running":
            return

        self._current_job_id = None
        self._show_menu()

    def _run_batch_add_ea(self):
        raw_input = self.batch_text.get("1.0", "end").strip()
        if not raw_input:
            self._append_warning("Please enter at least one Student ID.")
            return

        student_ids = self._parse_student_ids(raw_input)
        if student_ids is None:
            return
        if not student_ids:
            self._append_warning("No valid Student IDs remain to process.")
            return

        self._show_batch_output()

        try:
            self._current_job_id = self.controller.batch_add_ea(student_ids, requester=self)
        except Exception as exc:
            self.on_batch_add_ea_error(str(exc))
            return

        self._append_output(f"Starting Batch Add Enrollment Agreements for {len(student_ids)} student(s)...")

    def _parse_student_ids(self, raw_input: str) -> list[str] | None:
        tokens = [token for token in re.split(r"[\s,]+", raw_input) if token]
        valid_ids: list[str] = []

        for token in tokens:
            if token.isdigit() and len(token) == 10:
                valid_ids.append(token)
                continue

            should_continue = self._ask_continue_invalid_id(token)
            if not should_continue:
                return None

        return valid_ids

    def _ask_continue_invalid_id(self, student_id: str) -> bool:
        result = {"value": False}
        dialog = tk.Toplevel(self)
        dialog.title("Invalid ID")
        dialog.configure(bg="#C0C0C0")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        tk.Label(
            dialog,
            text=f"ID {student_id} is invalid. Continue?",
            bg="#C0C0C0",
            justify="left",
        ).grid(row=0, column=0, columnspan=2, padx=16, pady=(16, 12), sticky="w")

        cancel_btn = ActionButton(
            dialog,
            text="Cancel",
            icon=None,
            command=lambda: self._close_invalid_id_dialog(dialog, result, False),
            width=120,
            height=32,
        )
        cancel_btn.grid(row=1, column=0, padx=(16, 8), pady=(0, 16), sticky="e")

        continue_btn = ActionButton(
            dialog,
            text="Continue",
            icon=None,
            command=lambda: self._close_invalid_id_dialog(dialog, result, True),
            width=120,
            height=32,
        )
        continue_btn.grid(row=1, column=1, padx=(8, 16), pady=(0, 16), sticky="w")

        dialog.protocol(
            "WM_DELETE_WINDOW",
            lambda: self._close_invalid_id_dialog(dialog, result, False),
        )

        dialog.update_idletasks()
        root = self.winfo_toplevel()
        x = root.winfo_rootx() + (root.winfo_width() - dialog.winfo_reqwidth()) // 2
        y = root.winfo_rooty() + (root.winfo_height() - dialog.winfo_reqheight()) // 2
        dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        dialog.wait_window()
        return result["value"]

    def _close_invalid_id_dialog(self, dialog, result, value: bool):
        result["value"] = value
        dialog.destroy()

    def on_batch_add_ea_progress(self, message: str):
        self._append_output(message)

    def on_batch_add_ea_completed(self, _payload):
        self._append_output("Batch Add Enrollment Agreements finished.")
        self._current_job_id = None
        self._show_batch_done()

    def on_batch_add_ea_error(self, message: str):
        self._append_output(f"ERROR: {message}")
        self._current_job_id = None
        self._show_batch_done()

    def _append_output(self, message: str):
        self.batch_text.configure(state="normal")
        self.batch_text.insert("end", f"{message}\n")
        self.batch_text.see("end")
        self.batch_text.configure(state="disabled")

    def _append_warning(self, message: str):
        self.batch_text.configure(state="normal")
        self.batch_text.delete("1.0", "end")
        self.batch_text.insert("1.0", message)
        self.batch_text.see("end")
        self.batch_text.focus_set()

    def _set_action_button(
        self,
        *,
        text: str,
        command,
        enabled: bool,
        depressed: bool,
    ):
        self.action_btn.command = command
        self.action_btn.text_label.configure(text=text)
        self.action_btn.set_state("normal" if enabled else "disabled")
        self.action_btn.configure(relief="sunken" if depressed else "raised")
        if depressed:
            self.action_btn._set_bg_all(self.action_btn.disabled_bg)

    def _set_back_button_enabled(self, enabled: bool):
        self.back_btn.set_state("normal" if enabled else "disabled")

    def _get_batch_add_ea_button_size(self, parent):
        grid = 4
        base_width, base_height = self.controller.get_main_action_button_size()

        temp_button = tk.Button(
            parent,
            text="Batch Add Enrollment Agreements",
            image=self.controller.icons["batch_add_ea"],
            compound="left",
        )
        temp_button.grid(row=0, column=0)
        self.update_idletasks()

        required_width = temp_button.winfo_reqwidth()
        required_width += self.controller.icons["batch_add_ea"].width() + (grid * 12)
        required_height = temp_button.winfo_reqheight()

        temp_button.destroy()

        return max(base_width, required_width), max(base_height, required_height)

    def get_preferred_window_size(self):
        default_width, default_height = self.controller.get_default_window_size()
        self.update_idletasks()
        req_w = self.winfo_reqwidth() + 32
        req_h = self.winfo_reqheight() + 32
        return max(default_width, req_w), max(default_height, req_h)

    def get_max_preferred_window_size(self):
        default_width, default_height = self.controller.get_default_window_size()

        self.menu_frame.grid(row=0, column=0, sticky="nsew")
        self.batch_frame.grid(row=0, column=0, sticky="nsew")
        self.action_btn.grid()
        self.update_idletasks()
        req_w = self.winfo_reqwidth() + 32
        req_h = self.winfo_reqheight() + 32

        if self._mode == "menu":
            self.batch_frame.grid_remove()
            self.action_btn.grid_remove()
        else:
            self.menu_frame.grid_remove()

        self.update_idletasks()
        return max(default_width, req_w), max(default_height, req_h)
