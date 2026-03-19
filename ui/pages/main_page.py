import tkinter as tk
from ..widgets.action_button import ActionButton


class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#C0C0C0")
        self.controller = controller
        self._build()

    def _build(self):
        GRID = 4

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        title = tk.Label(
            self,
            text="OEG Automation Suite",
            bg="#C0C0C0"
        )
        title.grid(row=0, column=0, pady=(GRID * 4, 0), sticky="n")

        body = tk.Frame(self, bg="#C0C0C0")
        body.grid(row=1, column=0, sticky="nsew")

        body.grid_rowconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=0)
        body.grid_rowconfigure(2, weight=1)
        body.grid_columnconfigure(0, weight=1)

        btn_wrap = tk.Frame(body, bg="#C0C0C0")
        btn_wrap.grid(row=1, column=0)

        # Temporary stock buttons just to measure baseline size
        tmp_load = tk.Button(
            btn_wrap,
            text="Load Student by Student ID",
            image=self.controller.icons["load_id"],
            compound="left"
        )
        tmp_email = tk.Button(
            btn_wrap,
            text="Send Email",
            image=self.controller.icons["send_email"],
            compound="left"
        )
        tmp_tb = tk.Button(
            btn_wrap,
            text="Generate Tuition Breakdown",
            image=self.controller.icons["tuition_breakdown"],
            compound="left"
        )

        tmp_load.grid(row=0, column=0)
        tmp_email.grid(row=1, column=0)
        tmp_tb.grid(row=2, column=0)
        self.update_idletasks()

        max_icon_w = max(
            self.controller.icons["load_id"].width(),
            self.controller.icons["send_email"].width(),
            self.controller.icons["tuition_breakdown"].width()
        )

        btn_width = max(
            tmp_load.winfo_reqwidth(),
            tmp_email.winfo_reqwidth(),
            tmp_tb.winfo_reqwidth()
        ) + max_icon_w + (GRID * 12)

        btn_height = max(
            tmp_load.winfo_reqheight(),
            tmp_email.winfo_reqheight(),
            tmp_tb.winfo_reqheight()
        )

        tmp_load.destroy()
        tmp_email.destroy()
        tmp_tb.destroy()

        load_button = ActionButton(
            btn_wrap,
            text="Load Student by Student ID",
            icon=self.controller.icons["load_id"],
            command=self.load_student,
            width=btn_width,
            height=btn_height,
        )

        email_button = ActionButton(
            btn_wrap,
            text="Send Email",
            icon=self.controller.icons["send_email"],
            command=self.open_send_email_page,
            width=btn_width,
            height=btn_height,
        )

        tb_button = ActionButton(
            btn_wrap,
            text="Generate Tuition Breakdown",
            icon=self.controller.icons["tuition_breakdown"],
            command=self.open_tuition_breakdown,
            width=btn_width,
            height=btn_height,
        )

        load_button.grid(row=0, column=0, pady=GRID)
        email_button.grid(row=1, column=0, pady=GRID)
        tb_button.grid(row=2, column=0, pady=GRID)

    def load_student(self):
        self.controller.show_page("LoadStudentByIDPage")

    def open_send_email_page(self):
        self.controller.show_page("SendEmailPage")

    def open_tuition_breakdown(self):
        self.controller.show_page("GenerateTBPage")
