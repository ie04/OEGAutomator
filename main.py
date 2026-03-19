from automations.runner import AutomationRunner
from ui.automator_ui import AutomatorUI


if __name__ == "__main__":
    runner = AutomationRunner()
    runner.start()

    automator_ui = AutomatorUI(runner=runner)

    def on_close():
        runner.stop()
        automator_ui.destroy()

    automator_ui.protocol("WM_DELETE_WINDOW", on_close)
    automator_ui.mainloop()