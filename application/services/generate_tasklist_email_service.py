from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

PLACEHOLDER_RE = re.compile(r"\[\[([A-Z0-9_ ]+)\]\]")


@dataclass(frozen=True, slots=True)
class TaskListEmailRequest:
    first_name: str
    to_email: str
    student_id: str
    selected_tasks: tuple[str, ...]
    subject: str | None = None


class GenerateTasklistEmailService:
    ALL_TASKS_COMPLETE_MESSAGE = "All admissions documents complete. Good job!"
    BLOCK_CODES = (
        "HST", "HMT", "GIPI", "EA", "BSD", "CC", "SEI", "TCD", "COLT",
        "TAS", "TRA", "LNC", "PO", "NBC", "CEA", "MAD", "AA",
    )

    def __init__(
        self,
        oft_path: Path | None = None,
        blocks_html_path: Path | None = None,
    ) -> None:
        project_dir = Path(__file__).resolve().parents[2] / "automations" / "email_generator"
        self.oft_path = oft_path or (project_dir / "skeletons" / "Task List Base Template.oft")
        self.blocks_html_path = blocks_html_path or (project_dir / "blocks.html")

    def generate_email(self, request: TaskListEmailRequest) -> None:
        first_name = request.first_name.strip()
        to_email = request.to_email.strip()
        student_id = request.student_id.strip()
        selected_tasks = tuple(task.strip().upper() for task in request.selected_tasks if task.strip())

        if not first_name:
            raise ValueError("First Name is required.")
        if not first_name.isalpha():
            raise ValueError("First Name must contain letters only.")
        if not to_email:
            raise ValueError("E-mail is required.")
        if not student_id:
            raise ValueError("Student ID is required.")
        if not student_id.isdigit() or len(student_id) != 10:
            raise ValueError("Student ID must be exactly 10 digits.")

        if not self.oft_path.exists():
            raise FileNotFoundError(f"Template .oft not found: {self.oft_path}")
        if not self.blocks_html_path.exists():
            raise FileNotFoundError(f"blocks.html not found: {self.blocks_html_path}")

        blocks_map = self.load_blocks_map(self.blocks_html_path, list(self.BLOCK_CODES))
        values = {
            "NAME": first_name,
            "DEADLINE": self.compute_deadline_str(),
            "STUDENTID": student_id,
            "BLOCKS": self.build_blocks_html(list(selected_tasks), blocks_map),
        }

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
        mail.HTMLBody = self.apply_placeholders(html_body, values)
        mail.Display()
        inspector = mail.GetInspector
        inspector.Activate()

    @staticmethod
    def compute_deadline_str() -> str:
        today = date.today()
        candidate = today + timedelta(days=2)
        if candidate.weekday() == 6:
            candidate = today + timedelta(days=3)
        return f"{candidate.month}/{candidate.day}/{candidate.year}"

    @staticmethod
    def _level_from_style(style: str | None) -> int | None:
        if not style:
            return None
        match = re.search(r"level(\d+)", style)
        return int(match.group(1)) if match else None

    @classmethod
    def _build_nested_ul(cls, li_group):
        from lxml import etree

        root_ul = etree.Element("ul")
        stack = [(1, root_ul, None)]

        for src_li in li_group:
            level = cls._level_from_style(src_li.get("style")) or 1
            if level < 1:
                level = 1

            while level > stack[-1][0]:
                parent_level, _parent_ul, parent_last_li = stack[-1]
                if parent_last_li is None:
                    break
                new_ul = etree.Element("ul")
                parent_last_li.append(new_ul)
                stack.append((parent_level + 1, new_ul, None))

            while level < stack[-1][0]:
                stack.pop()

            current_ul = stack[-1][1]
            li_copy = copy.deepcopy(src_li)
            current_ul.append(li_copy)
            stack[-1] = (stack[-1][0], current_ul, li_copy)

        return root_ul

    @classmethod
    def load_blocks_map(
        cls,
        blocks_html_path: Path,
        block_codes: list[str],
    ) -> dict[str, str]:
        try:
            from lxml import etree
            from lxml import html as lxml_html
        except ImportError as exc:
            raise RuntimeError(
                "lxml is required to build the task list email body. Install it in your .venv first."
            ) from exc

        raw = blocks_html_path.read_text(encoding="utf-8", errors="ignore")
        doc = lxml_html.fromstring(raw)
        lis = doc.xpath("//li")

        blocks = []
        current = []
        for li in lis:
            level = cls._level_from_style(li.get("style"))
            if level == 1:
                if current:
                    blocks.append(current)
                current = [li]
            elif current:
                current.append(li)
        if current:
            blocks.append(current)

        if len(blocks) != len(block_codes):
            raise RuntimeError(
                f"Expected {len(block_codes)} main blocks, found {len(blocks)}. "
                "blocks.html format may have changed."
            )

        out = {}
        for code, li_group in zip(block_codes, blocks):
            nested_ul = cls._build_nested_ul(li_group)
            out[code] = etree.tostring(nested_ul, encoding="unicode", method="html")
        return out

    @staticmethod
    def apply_placeholders(html: str, values: dict[str, str]) -> str:
        normalized = {key.replace(" ", "").upper(): value for key, value in values.items()}

        def repl(match: re.Match) -> str:
            key_norm = match.group(1).replace(" ", "").upper()
            return normalized.get(key_norm, match.group(0))

        return PLACEHOLDER_RE.sub(repl, html)

    @classmethod
    def build_blocks_html(
        cls,
        selected_codes: list[str],
        blocks_map: dict[str, str],
    ) -> str:
        if not selected_codes:
            return cls.ALL_TASKS_COMPLETE_MESSAGE

        parts: list[str] = []
        for code_value in selected_codes:
            code = code_value.upper()
            if code not in blocks_map:
                raise ValueError(
                    f"Unknown block code: {code_value}. "
                    f"Valid: {', '.join(cls.BLOCK_CODES)}"
                )
            parts.append(blocks_map[code])
        return "\n".join(parts)
