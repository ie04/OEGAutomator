import tkinter as tk
from ..widgets.action_button import ActionButton


class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#C0C0C0")
        self.controller = controller
        self._build()

    def _build(self):
        GRID = 4

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        body = tk.LabelFrame(
            self,
            text="",
            bg="#C0C0C0",
            padx=16,
            pady=12,
        )
        body.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 12))

        title = tk.Label(
            self,
            text="OEG Automation Suite",
            bg="#C0C0C0",
            font=("W95FA", -32),
        )
        title.place(in_=body, relx=0.5, y=-10, anchor="center")

        body.grid_rowconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=0)
        body.grid_rowconfigure(2, weight=1)
        body.grid_columnconfigure(0, weight=1)

        btn_wrap = tk.Frame(body, bg="#C0C0C0")
        btn_wrap.grid(row=1, column=0)

        btn_width, btn_height = self.controller.get_main_action_button_size()

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

        salesforce_helpers_button = ActionButton(
            btn_wrap,
            text="Salesforce Helpers",
            icon=self.controller.icons["salesforce_helpers"],
            command=self.open_salesforce_helpers,
            width=btn_width,
            height=btn_height,
        )

        load_button.grid(row=0, column=0, pady=GRID)
        email_button.grid(row=1, column=0, pady=GRID)
        tb_button.grid(row=2, column=0, pady=GRID)
        salesforce_helpers_button.grid(row=3, column=0, pady=GRID)

    def load_student(self):
        self.controller.show_page("LoadStudentByIDPage")

    def open_send_email_page(self):
        self.controller.show_page("SendEmailPage")

    def open_tuition_breakdown(self):
        self.controller.show_page("GenerateTBPage")

    def open_salesforce_helpers(self):
        self.controller.show_page("SalesforceHelpersPage")
