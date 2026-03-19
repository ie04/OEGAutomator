from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


PLACEHOLDER_RE = re.compile(r"\[\[([A-Z0-9_ ]+)\]\]")


@dataclass(frozen=True, slots=True)
class EstFinAidEmailRequest:
    first_name: str
    to_email: str
    start_date: str
    attachment_path: str
    subject: str | None = None


class GenerateEstFinAidEmailService:
    def __init__(self, oft_path: Path | None = None) -> None:
        project_dir = Path(__file__).resolve().parents[2] / "automations" / "email_automator"
        self.oft_path = oft_path or (
            project_dir / "skeletons" / "Estimated Financial Aid Breakdown Template.oft"
        )

    def generate_email(self, request: EstFinAidEmailRequest) -> None:
        first_name = request.first_name.strip()
        to_email = request.to_email.strip()
        start_date = request.start_date.strip()
        attachment_value = request.attachment_path.strip()

        if not first_name:
            raise ValueError("First Name is required.")
        if not first_name.isalpha():
            raise ValueError("First Name must contain letters only.")
        if not to_email:
            raise ValueError("E-mail is required.")
        if not start_date:
            raise ValueError("Start Date is required.")
        if not attachment_value:
            raise ValueError("A PDF attachment is required.")

        attachment_path = Path(attachment_value).expanduser()
        if attachment_path.suffix.lower() != ".pdf":
            raise ValueError("Attachment must be a PDF file.")
        if not attachment_path.exists():
            raise FileNotFoundError(f"Attachment not found: {attachment_path}")
        if not self.oft_path.exists():
            raise FileNotFoundError(f"Template .oft not found: {self.oft_path}")

        try:
            import win32com.client
        except ImportError as exc:
            raise RuntimeError(
                "pywin32 is required to open Outlook. Install it in your .venv first."
            ) from exc

        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItemFromTemplate(str(self.oft_path))
        mail.To = to_email
        if request.subject:
            mail.Subject = request.subject

        html_body = mail.HTMLBody or ""
        mail.HTMLBody = self.apply_placeholders(
            html_body,
            {"NAME": first_name, "STARTDATE": start_date},
        )
        mail.Attachments.Add(str(attachment_path.resolve()))
        mail.Display()
        inspector = mail.GetInspector
        inspector.Activate()

    @staticmethod
    def apply_placeholders(html: str, values: dict[str, str]) -> str:
        normalized = {key.replace(" ", "").upper(): value for key, value in values.items()}

        def repl(match: re.Match) -> str:
            key_norm = match.group(1).replace(" ", "").upper()
            return normalized.get(key_norm, match.group(0))

        return PLACEHOLDER_RE.sub(repl, html)
