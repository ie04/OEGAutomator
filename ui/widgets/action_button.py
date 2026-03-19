import tkinter as tk


class ActionButton(tk.Frame):
    def __init__(
        self,
        parent,
        text,
        icon,
        command,
        width=260,
        height=40,
        bg="#C0C0C0",
        hover_bg="#CDCDCD",
        active_bg="#A0A0A0",
        disabled_bg="#D9D9D9",
        disabled_fg="#7A7A7A",
        borderwidth=2,
        relief="raised",
        state="normal",
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=bg,
            bd=borderwidth,
            relief=relief
        )

        self.command = command
        self.state = state
        self.default_bg = bg
        self.hover_bg = hover_bg
        self.active_bg = active_bg
        self.disabled_bg = disabled_bg
        self.disabled_fg = disabled_fg
        self._is_pressed = False
        self._icon = icon  # keep reference

        self.grid_propagate(False)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)  # icon
        self.grid_columnconfigure(1, weight=1)  # centered text
        self.grid_columnconfigure(2, weight=0)  # balancing spacer

        if icon:
            self.icon_label = tk.Label(self, image=icon, bg=bg)
            self.icon_label.grid(row=0, column=0, padx=(8, 0), sticky="w")

            icon_w = icon.width()
            self.spacer = tk.Frame(self, bg=bg, width=icon_w, height=1)
            self.spacer.grid(row=0, column=2, padx=(0, 8), sticky="ns")
            self.spacer.grid_propagate(False)
        else:
            self.icon_label = None
        
        self.text_label = tk.Label(self, text=text, bg=bg, anchor="center")
        self.text_label.grid(row=0, column=1, sticky="nsew", padx=(8, 8))

        self._bind_recursive(self)
        self.set_state(state)

    def _bind_recursive(self, widget):
        for sequence, handler in (
            ("<Enter>", self._on_enter),
            ("<Leave>", self._on_leave),
            ("<ButtonPress-1>", self._on_press),
            ("<ButtonRelease-1>", self._on_release),
        ):
            widget.bind(sequence, handler)

        for child in widget.winfo_children():
            self._bind_recursive(child)

    def _set_bg_all(self, color):
        self.configure(bg=color)
        for child in self.winfo_children():
            child.configure(bg=color)

    def set_state(self, state):
        self.state = state
        is_disabled = state == "disabled"
        relief = "sunken" if self._is_pressed and not is_disabled else "raised"
        text_fg = self.disabled_fg if is_disabled else "black"
        bg = self.disabled_bg if is_disabled else self.default_bg

        self._is_pressed = False
        self.configure(relief=relief)
        self._set_bg_all(bg)
        self.text_label.configure(fg=text_fg)

    def _pointer_inside(self):
        x = self.winfo_pointerx() - self.winfo_rootx()
        y = self.winfo_pointery() - self.winfo_rooty()
        return 0 <= x < self.winfo_width() and 0 <= y < self.winfo_height()

    def _on_enter(self, event=None):
        if self.state == "disabled":
            return
        if not self._is_pressed:
            self._set_bg_all(self.hover_bg)

    def _on_leave(self, event=None):
        if self.state == "disabled":
            return
        if not self._is_pressed:
            self.configure(relief="raised")
            self._set_bg_all(self.default_bg)

    def _on_press(self, event=None):
        if self.state == "disabled":
            return
        self._is_pressed = True
        self.configure(relief="sunken")
        self._set_bg_all(self.active_bg)

    def _on_release(self, event=None):
        if self.state == "disabled":
            return
        if not self._is_pressed:
            return

        was_inside = self._pointer_inside()
        self._is_pressed = False
        self.configure(relief="raised")

        if was_inside:
            self._set_bg_all(self.hover_bg)
            self.command()
        else:
            self._set_bg_all(self.default_bg)
