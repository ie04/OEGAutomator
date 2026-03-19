import argparse
from pathlib import Path

from application.services.generate_tasklist_email_service import (
    GenerateTasklistEmailService,
    TaskListEmailRequest,
)


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_OFT = PROJECT_DIR / "skeletons" / "Task List Base Template.oft"
DEFAULT_BLOCKS = PROJECT_DIR / "blocks.html"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Outlook task-list email from an .oft template and block codes."
    )
    parser.add_argument("to_email", help="Recipient email address for the To field")
    parser.add_argument("name", help="Replaces [[NAME]]")
    parser.add_argument("studentid", help="Replaces [[STUDENTID]]")
    parser.add_argument(
        "codes",
        nargs="*",
        help="Any number of block codes (e.g. HST GIPI EA)",
    )
    parser.add_argument(
        "--oft",
        default=str(DEFAULT_OFT),
        help="Path to your base .oft template (default: project folder)",
    )
    parser.add_argument(
        "--blocks",
        default=str(DEFAULT_BLOCKS),
        help="Path to blocks.html (default: project folder)",
    )
    parser.add_argument(
        "--subject",
        default=None,
        help="Optional subject override",
    )

    args = parser.parse_args()
    service = GenerateTasklistEmailService(
        oft_path=Path(args.oft).expanduser().resolve(),
        blocks_html_path=Path(args.blocks).expanduser().resolve(),
    )

    try:
        service.generate_email(
            TaskListEmailRequest(
                first_name=args.name,
                to_email=args.to_email,
                student_id=args.studentid,
                selected_tasks=tuple(args.codes),
                subject=args.subject,
            )
        )
        return 0
    except Exception as exc:
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
