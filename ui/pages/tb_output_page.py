import tkinter as tk

from ..widgets.action_button import ActionButton


class TBOutputPage(tk.Toplevel):
    def __init__(self, parent, output_text: str):
        super().__init__(parent)
        self.title("TB Output")
        self.configure(bg="#C0C0C0")
        self.geometry("560x420")
        self.minsize(520, 360)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)

        content = tk.Frame(self, bg="#C0C0C0")
        content.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 8))
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        self.text = tk.Text(
            content,
            wrap="word",
            undo=True,
        )
        self.text.grid(row=0, column=0, sticky="nsew")
        self.text.insert("1.0", output_text)

        scrollbar = tk.Scrollbar(content, orient="vertical", command=self.text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(8, 0))
        self.text.configure(yscrollcommand=scrollbar.set)

        bottom = tk.Frame(self, bg="#C0C0C0")
        bottom.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=0)

        done_button = ActionButton(
            bottom,
            text="Done",
            icon=None,
            command=self.destroy,
            width=120,
            height=32,
        )
        done_button.grid(row=0, column=1, sticky="e")

        self.after_idle(self.text.focus_set)
