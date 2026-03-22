from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from automations.tuition_breakdown_generator import generate_tb

try:
    import pythoncom
except ImportError:  # pragma: no cover - only relevant on Windows with pywin32 missing
    pythoncom = None


@dataclass(frozen=True, slots=True)
class TuitionBreakdownResult:
    template_path: Path
    pdf_path: Path | None
    c4_value: str
    d4_value: str
    pdf_sheet_name: str | None
    output_text: str


class GenerateTutionBreakdownService:
    def __init__(self, project_dir: Path | None = None) -> None:
        self.project_dir = project_dir or generate_tb.PROJECT_DIR

    def generate_tuition_breakdown(
        self,
        *,
        start_date: str,
        program_code: str,
        sai: str,
        student_number: str,
        student_name: str,
        dep_ind: str,
        tas: bool = False,
        ind_override: str | None = None,
        completer_program_code: str | None = None,
        nostaff: bool = False,
        staff_used_ind: str | None = None,
        staff_used_dep: str | None = None,
        has_bs: bool = False,
        crossover_sai: str | None = None,
        pell_used: str | None = None,
        file: str | None = None,
        outdir: str = "out",
    ) -> TuitionBreakdownResult:
        com_initialized = False
        if pythoncom is not None:
            pythoncom.CoInitialize()
            com_initialized = True

        try:
            return self._generate_tuition_breakdown_impl(
                start_date=start_date,
                program_code=program_code,
                sai=sai,
                student_number=student_number,
                student_name=student_name,
                dep_ind=dep_ind,
                tas=tas,
                ind_override=ind_override,
                completer_program_code=completer_program_code,
                nostaff=nostaff,
                staff_used_ind=staff_used_ind,
                staff_used_dep=staff_used_dep,
                has_bs=has_bs,
                crossover_sai=crossover_sai,
                pell_used=pell_used,
                file=file,
                outdir=outdir,
            )
        finally:
            if com_initialized:
                pythoncom.CoUninitialize()

    def _generate_tuition_breakdown_impl(
        self,
        *,
        start_date: str,
        program_code: str,
        sai: str,
        student_number: str,
        student_name: str,
        dep_ind: str,
        tas: bool = False,
        ind_override: str | None = None,
        completer_program_code: str | None = None,
        nostaff: bool = False,
        staff_used_ind: str | None = None,
        staff_used_dep: str | None = None,
        has_bs: bool = False,
        crossover_sai: str | None = None,
        pell_used: str | None = None,
        file: str | None = None,
        outdir: str = "out",
    ) -> TuitionBreakdownResult:
        parsed_start_date = generate_tb.parse_start_date(start_date)

        normalized_program_code = program_code.strip().upper()
        if not normalized_program_code:
            raise ValueError("Program Code is required.")

        parsed_sai = generate_tb.parse_sai(sai)
        parsed_student_number = generate_tb.parse_student_number(student_number)
        parsed_student_name = generate_tb.parse_student_name(student_name)
        parsed_dep_ind = generate_tb.parse_dep_ind(dep_ind)

        normalized_ind_override = self._normalize_optional_text(ind_override)
        if normalized_ind_override is not None:
            normalized_ind_override = generate_tb.parse_ind_override(normalized_ind_override)

        normalized_completer_program_code = self._normalize_optional_text(
            completer_program_code
        )
        if normalized_completer_program_code is not None:
            normalized_completer_program_code = generate_tb.parse_completer_program_code(
                normalized_completer_program_code
            )

        money_parser_ind = generate_tb.parse_money_in_range(0, 57500)
        money_parser_dep = generate_tb.parse_money_in_range(0, 31000)
        parsed_staff_used_ind = self._parse_optional_value(staff_used_ind, money_parser_ind)
        parsed_staff_used_dep = self._parse_optional_value(staff_used_dep, money_parser_dep)
        parsed_crossover_sai = self._parse_optional_value(crossover_sai, generate_tb.parse_sai)
        parsed_pell_used = self._parse_optional_value(pell_used, generate_tb.parse_pell_used)

        normalized_file = self._normalize_optional_text(file)
        normalized_outdir = outdir.strip() or "out"

        if normalized_ind_override is not None and parsed_dep_ind != "DEP":
            raise ValueError("--ind can only be used when dep_ind is DEP.")
        if nostaff and parsed_staff_used_ind is not None:
            raise ValueError(
                "--nostaff cannot be used together with --staff-used-ind."
            )
        if nostaff and parsed_staff_used_dep is not None:
            raise ValueError(
                "--nostaff cannot be used together with --staff-used-dep."
            )
        if os.name != "nt":
            raise RuntimeError("This workflow requires Windows + Excel + pywin32.")

        template_path = generate_tb.resolve_template_path(normalized_file)

        outdir_path = (self.project_dir / normalized_outdir).resolve()
        outdir_path.mkdir(parents=True, exist_ok=True)

        safe_student_name = generate_tb.sanitize_filename_component(parsed_student_name)
        safe_program_code = generate_tb.sanitize_filename_component(normalized_program_code)
        pdf_filename = (
            f"{parsed_student_number} {safe_student_name} {safe_program_code} TB.pdf"
        )
        out_pdf = outdir_path / pdf_filename

        c4_value, d4_value, output_text, selected_sheet_name = (
            generate_tb.fill_save_and_optionally_export_pdf(
            template_path=template_path,
            out_pdf=out_pdf,
            start_date=parsed_start_date,
            program_code=normalized_program_code,
            sai=parsed_sai,
            dep_ind=parsed_dep_ind,
            tas=tas,
            ind_override=normalized_ind_override,
            completer_program_code=normalized_completer_program_code,
            nostaff=nostaff,
            staff_used_ind=parsed_staff_used_ind,
            staff_used_dep=parsed_staff_used_dep,
            has_bs=has_bs,
            crossover_sai=parsed_crossover_sai,
            pell_used=parsed_pell_used,
            sheet_name="4 ACYR Breakdown",
            do_pdf=True,
            )
        )

        pdf_sheet_name = selected_sheet_name or generate_tb.choose_breakdown_sheet(
            d4_value,
            "4 ACYR Breakdown",
            completer_program_code=normalized_completer_program_code,
        )
        pdf_path = out_pdf

        generate_tb.open_pdf_in_adobe(pdf_path)

        return TuitionBreakdownResult(
            template_path=template_path,
            pdf_path=pdf_path,
            c4_value=c4_value,
            d4_value=d4_value,
            pdf_sheet_name=pdf_sheet_name,
            output_text=output_text,
        )

    @staticmethod
    def _normalize_optional_text(value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None

    @classmethod
    def _parse_optional_value(cls, value: str | None, parser):
        normalized = cls._normalize_optional_text(value)
        if normalized is None:
            return None
        return parser(normalized)
