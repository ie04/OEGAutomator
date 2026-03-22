#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

import tkinter as tk
from tkinter import messagebox


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = PROJECT_DIR / "TB Template 2.2.0 Update_2025-2026.xlsm"

_MDYYYY_RE = re.compile(r"^(0?[1-9]|1[0-2])/(0?[1-9]|[12]\d|3[01])/\d{4}$")
_STUDENT_NUM_RE = re.compile(r"^\d{10}$")


def parse_start_date(s: str) -> dt.date:
    s = s.strip()
    if not _MDYYYY_RE.match(s):
        raise argparse.ArgumentTypeError(
            "start_date must be in M/D/YYYY format like 3/2/2026."
        )
    try:
        return dt.datetime.strptime(s, "%m/%d/%Y").date()
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Invalid calendar date: '{s}'.") from e


def parse_sai(s: str) -> int:
    try:
        v = int(s.replace(",", "").strip())
    except ValueError as e:
        raise argparse.ArgumentTypeError("SAI must be an integer.") from e
    if v < -1500 or v > 999_999:
        raise argparse.ArgumentTypeError("SAI must be between -1500 and 999999.")
    return v


def parse_student_number(s: str) -> str:
    s = s.strip()
    if not _STUDENT_NUM_RE.match(s):
        raise argparse.ArgumentTypeError("student_number must be exactly 10 digits.")
    return s


def parse_student_name(s: str) -> str:
    s = s.strip()
    if not s:
        raise argparse.ArgumentTypeError("student_name cannot be empty.")
    return s


def parse_dep_ind(s: str) -> str:
    s = s.strip().upper()
    if s not in {"DEP", "IND"}:
        raise argparse.ArgumentTypeError("dep_ind must be either DEP or IND.")
    return s


def parse_ind_override(s: str) -> str:
    s = s.strip().upper()
    allowed = {"ACYR1", "ACYR2", "ACYR3", "ACYR4"}
    if s not in allowed:
        raise argparse.ArgumentTypeError(
            "--ind must be one of: ACYR1, ACYR2, ACYR3, ACYR4"
        )
    return s


def parse_completer_program_code(s: str) -> str:
    s = s.strip().upper()
    if not s:
        raise argparse.ArgumentTypeError("--completer requires a program code.")
    return s


def parse_money_in_range(min_value: float, max_value: float):
    def _parser(s: str) -> float:
        s = s.strip().replace(",", "")
        try:
            value = float(s)
        except ValueError as e:
            raise argparse.ArgumentTypeError("Value must be a number.") from e

        if value < min_value or value > max_value:
            raise argparse.ArgumentTypeError(
                f"Value must be between {min_value:g} and {max_value:g}."
            )

        if round(value, 2) != value:
            raise argparse.ArgumentTypeError(
                "Value may have at most 2 decimal places."
            )

        return round(value, 2)

    return _parser


def parse_pell_used(s: str) -> float:
    s = s.strip().replace(",", "")
    try:
        value = float(s)
    except ValueError as e:
        raise argparse.ArgumentTypeError("--pell-used must be a number.") from e

    value = round(value, 3)

    if value < 0.000 or value > 600.000:
        raise argparse.ArgumentTypeError("--pell-used must be between 0.000 and 600.000.")

    return value


def norm_str(x) -> str:
    if x is None:
        return ""
    return str(x).strip()


def sanitize_filename_component(s: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", s).strip()


def excel_serial_to_date(value) -> Optional[dt.date]:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    return None


def resolve_template_path(user_supplied_path: Optional[str]) -> Path:
    if user_supplied_path:
        template_path = Path(user_supplied_path).expanduser().resolve()
    else:
        template_path = DEFAULT_TEMPLATE.resolve()

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}.")
    return template_path


def ask_open_pdf(pdf_path: Path) -> bool:
    root = tk.Tk()
    root.withdraw()
    try:
        return messagebox.askyesno(
            title="Open PDF?",
            message=f"PDF saved:\n\n{pdf_path}\n\nWould you like to open it now in Adobe Acrobat?",
        )
    finally:
        root.destroy()


def find_adobe_acrobat_exe() -> Optional[Path]:
    candidates = [
        r"C:\Program Files\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
        r"C:\Program Files (x86)\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
        r"C:\Program Files\Adobe\Acrobat Reader\Reader\AcroRd32.exe",
        r"C:\Program Files (x86)\Adobe\Acrobat Reader\Reader\AcroRd32.exe",
        r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe",
        r"C:\Program Files (x86)\Adobe\Acrobat DC\Acrobat\Acrobat.exe",
        r"C:\Program Files\Adobe\Acrobat\Acrobat\Acrobat.exe",
        r"C:\Program Files (x86)\Adobe\Acrobat\Acrobat\Acrobat.exe",
    ]
    for p in candidates:
        exe = Path(p)
        if exe.exists():
            return exe
    return None


def open_pdf_in_adobe(pdf_path: Path) -> None:
    exe = find_adobe_acrobat_exe()
    if exe is None:
        raise FileNotFoundError("Could not find Adobe Acrobat/Reader.")
    subprocess.Popen([str(exe), str(pdf_path)], close_fds=True)


def wait_for_excel_calculation(excel, timeout_seconds: float = 120.0) -> None:
    xl_done = 0
    start = time.time()
    while excel.CalculationState != xl_done:
        time.sleep(0.1)
        if time.time() - start > timeout_seconds:
            raise TimeoutError("Excel calculation did not finish before timeout.")


def find_master_row_excel(
    ws_master,
    start_date: dt.date,
    program_code: str,
    header_row: int = 1,
) -> Optional[int]:
    target_code = norm_str(program_code).upper()
    last_row = ws_master.Cells(ws_master.Rows.Count, 1).End(-4162).Row

    for r in range(header_row + 1, last_row + 1):
        a_val = excel_serial_to_date(ws_master.Cells(r, 1).Value)
        if a_val != start_date:
            continue

        h_val = norm_str(ws_master.Cells(r, 8).Value).upper()
        if h_val == target_code:
            return r
    return None


def choose_breakdown_sheet(
    d4_value: str,
    default_sheet: str,
    completer_program_code: Optional[str] = None,
) -> str:
    if completer_program_code is not None:
        return "4 ACYR Breakdown"

    d4_norm = norm_str(d4_value).upper()
    if d4_norm in {"ASSOCIATE", "AAS"}:
        return "2 ACYR Breakdown"
    return default_sheet


def get_breakdown_output_text(
    ws_breakdown,
    sheet_name: str,
    program_code: str,
    dep_ind: str,
    ind_override: Optional[str] = None,
    completer_program_code: Optional[str] = None,
) -> str:
    def cell_text(cell_ref: str) -> str:
        return norm_str(ws_breakdown.Range(cell_ref).Text)

    if dep_ind == "IND":
        ind_flag = "IND Y"
    elif ind_override is not None:
        ind_flag = f"IND N ({ind_override})"
    else:
        ind_flag = "IND N"

    sd_prog = program_code
    if completer_program_code is not None and sheet_name == "4 ACYR Breakdown":
        sd_prog = f"{program_code}/{completer_program_code}"

    if sheet_name == "4 ACYR Breakdown":
        lines = [
            "FA Breakdown",
            f"Ovl Bal: {cell_text('H55')} {ind_flag}",
            f"SD/Prog: {sd_prog}",
            f"1st Year Total Tuition: {cell_text('H6')}",
            f"1st AC YR Bal: {cell_text('H24')}",
            f"2nd AC YR Bal: {cell_text('H42')}",
            f"3rd AC YR Bal: {cell_text('E53')}",
            f"4th AC YR Bal: {cell_text('H53')}",
            "CA STRF: 0",
            f"Pell: {cell_text('H10')}",
            f"Comb Staff: {cell_text('H16')}",
            f"TAS/OMS: {cell_text('H22')}",
            "VA: 0",
            "MTA: 0",
            "Gap Funding:",
        ]
        return "\n".join(lines)

    if sheet_name == "2 ACYR Breakdown":
        lines = [
            "FA Breakdown",
            f"Ovl Bal: {cell_text('H45')} {ind_flag}",
            f"SD/Prog: {sd_prog}",
            f"1st Year Total Tuition: {cell_text('H6')}",
            f"1st AC YR Bal: {cell_text('H24')}",
            f"2nd AC YR Bal: {cell_text('H43')}",
            "CA STRF: 0",
            f"Pell: {cell_text('H10')}",
            f"Comb Staff: {cell_text('H16')}",
            f"TAS/OMS: {cell_text('H22')}",
            "VA: 0",
            "MTA: 0",
            "Gap Funding:",
        ]
        return "\n".join(lines)

    raise ValueError(f"Unsupported breakdown sheet for output text: '{sheet_name}'")


def fill_program_stafford_selection_excel(
    wb,
    start_date: dt.date,
    program_code: str,
    sai: int,
    dep_ind: str,
    tas: bool = False,
    ind_override: Optional[str] = None,
    completer_program_code: Optional[str] = None,
    nostaff: bool = False,
    staff_used_ind: Optional[float] = None,
    staff_used_dep: Optional[float] = None,
    has_bs: bool = False,
    crossover_sai: Optional[int] = None,
    pell_used: Optional[float] = None,
) -> Tuple[str, str]:
    ws_master = wb.Worksheets("MASTER")
    ws_sel = wb.Worksheets("Program & Stafford Selection")

    match_row = find_master_row_excel(ws_master, start_date, program_code)
    if match_row is None:
        raise LookupError(
            f"No match found in MASTER for start date {start_date.isoformat()} and program code '{program_code}'."
        )

    master_e = ws_master.Cells(match_row, 5).Value
    master_f = ws_master.Cells(match_row, 6).Value

    ws_sel.Range("B4").Value = start_date.strftime("%m/%d/%Y")
    ws_sel.Range("C4").Value = master_e
    ws_sel.Range("D4").Value = master_f
    ws_sel.Range("C43").Value = sai

    base_text = "Dependent" if dep_ind == "DEP" else "Independent"
    acyr_cells = ["G35", "G36", "G37", "G38"]

    for cell in acyr_cells:
        ws_sel.Range(cell).Value = base_text

    if ind_override is not None:
        if dep_ind != "DEP":
            raise ValueError("--ind can only be used when dep_ind is DEP.")
        start_index_map = {"ACYR1": 0, "ACYR2": 1, "ACYR3": 2, "ACYR4": 3}
        start_idx = start_index_map[ind_override]
        for cell in acyr_cells[start_idx:]:
            ws_sel.Range(cell).Value = "Independent"

    if tas:
        ws_sel.Range("N24").Value = "Yes"

    if nostaff:
        ws_sel.Range("E25").Value = 57500
        ws_sel.Range("D25").Value = 31000
    else:
        if staff_used_ind is not None:
            ws_sel.Range("E25").Value = staff_used_ind
        if staff_used_dep is not None:
            ws_sel.Range("D25").Value = staff_used_dep

    if has_bs:
        ws_sel.Range("B43").Value = "Yes"

    if crossover_sai is not None:
        e42_text = norm_str(ws_sel.Range("E42").Value).upper()
        if e42_text != "SAI 2":
            raise ValueError("Supplied start date is not in crossover")
        ws_sel.Range("E43").Value = crossover_sai

    if pell_used is not None:
        ws_sel.Range("B49").Value = pell_used
        ws_sel.Range("B49").NumberFormat = "0.000"

    d4_norm = norm_str(master_f).upper()

    if completer_program_code is not None:
        if d4_norm not in {"ASSOCIATE", "AAS"}:
            raise ValueError(
                "--completer can only be used when D4 resolves to Associate or AAS."
            )

        completer_row = find_master_row_excel(
            ws_master=ws_master,
            start_date=start_date,
            program_code=completer_program_code,
        )
        if completer_row is None:
            raise LookupError(
                f"No completer match found in MASTER for start date {start_date.isoformat()} and program code '{completer_program_code}'."
            )

        completer_e = ws_master.Cells(completer_row, 5).Value
        completer_f = ws_master.Cells(completer_row, 6).Value

        ws_sel.Range("C14").Value = completer_e
        ws_sel.Range("D14").Value = completer_f

    return norm_str(master_e), norm_str(master_f)


def fill_save_and_optionally_export_pdf(
    template_path: Path,
    out_pdf: Path,
    start_date: dt.date,
    program_code: str,
    sai: int,
    dep_ind: str,
    tas: bool,
    ind_override: Optional[str],
    completer_program_code: Optional[str],
    nostaff: bool,
    staff_used_ind: Optional[float],
    staff_used_dep: Optional[float],
    has_bs: bool,
    crossover_sai: Optional[int],
    pell_used: Optional[float],
    sheet_name: str,
    do_pdf: bool,
) -> Tuple[str, str, str, Optional[str]]:
    import win32com.client  # type: ignore

    xl_calculation_automatic = -4105
    xl_type_pdf = 0
    xl_quality_standard = 0

    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    try:
        wb = excel.Workbooks.Open(str(template_path))
        try:
            c4_val, d4_val = fill_program_stafford_selection_excel(
                wb=wb,
                start_date=start_date,
                program_code=program_code,
                sai=sai,
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
            )

            excel.Calculation = xl_calculation_automatic
            wb.RefreshAll()

            try:
                excel.CalculateUntilAsyncQueriesDone()
            except Exception:
                pass

            excel.CalculateFullRebuild()
            wait_for_excel_calculation(excel)
            time.sleep(0.5)

            output_text = ""
            selected_sheet_name = None
            if do_pdf:
                selected_sheet_name = choose_breakdown_sheet(
                    d4_val,
                    sheet_name,
                    completer_program_code=completer_program_code,
                )

                try:
                    ws = wb.Worksheets(selected_sheet_name)
                except Exception as e:
                    raise KeyError(f"Sheet not found: '{selected_sheet_name}'") from e

                out_pdf.parent.mkdir(parents=True, exist_ok=True)

                excel.CalculateFullRebuild()
                wait_for_excel_calculation(excel)
                time.sleep(0.5)

                output_text = get_breakdown_output_text(
                    ws,
                    selected_sheet_name,
                    program_code,
                    dep_ind,
                    ind_override=ind_override,
                    completer_program_code=completer_program_code,
                )

                ws.ExportAsFixedFormat(
                    Type=xl_type_pdf,
                    Filename=str(out_pdf),
                    Quality=xl_quality_standard,
                    IncludeDocProperties=True,
                    IgnorePrintAreas=False,
                    OpenAfterPublish=False,
                )

                time.sleep(0.5)

                if not out_pdf.exists():
                    raise RuntimeError(
                        f"Excel export completed, but the PDF was not found at: {out_pdf}"
                    )

            return c4_val, d4_val, output_text, selected_sheet_name

        finally:
            wb.Close(SaveChanges=False)
    finally:
        excel.Quit()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("start_date", type=parse_start_date)
    parser.add_argument("program_code")
    parser.add_argument("sai", type=parse_sai)
    parser.add_argument("student_number", type=parse_student_number)
    parser.add_argument("student_name", type=parse_student_name)
    parser.add_argument("dep_ind", type=parse_dep_ind)

    parser.add_argument("--tas", action="store_true")
    parser.add_argument("--ind", dest="ind_override", type=parse_ind_override, default=None)
    parser.add_argument(
        "--completer",
        dest="completer_program_code",
        type=parse_completer_program_code,
        default=None,
    )
    parser.add_argument("--nostaff", action="store_true")
    parser.add_argument(
        "--staff-used-ind",
        dest="staff_used_ind",
        type=parse_money_in_range(0, 57500),
        default=None,
    )
    parser.add_argument(
        "--staff-used-dep",
        dest="staff_used_dep",
        type=parse_money_in_range(0, 31000),
        default=None,
    )
    parser.add_argument("--has-bs", action="store_true")
    parser.add_argument(
        "--crossover-sai",
        dest="crossover_sai",
        type=parse_sai,
        default=None,
    )
    parser.add_argument(
        "--pell-used",
        dest="pell_used",
        type=parse_pell_used,
        default=None,
    )
    parser.add_argument("--file", default=None)
    parser.add_argument("--outdir", default="out")
    parser.add_argument("--no-pdf", action="store_true")
    parser.add_argument("--sheet", default="4 ACYR Breakdown")

    args = parser.parse_args()

    outdir = (PROJECT_DIR / args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    try:
        template_path = resolve_template_path(args.file)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    program_code = args.program_code.strip().upper()
    if not program_code:
        print("ERROR: program_code cannot be empty.", file=sys.stderr)
        return 2

    if args.ind_override is not None and args.dep_ind != "DEP":
        print("ERROR: --ind can only be used when dep_ind is DEP.", file=sys.stderr)
        return 2

    if args.nostaff and args.staff_used_ind is not None:
        print("ERROR: --nostaff cannot be used together with --staff-used-ind.", file=sys.stderr)
        return 2

    if args.nostaff and args.staff_used_dep is not None:
        print("ERROR: --nostaff cannot be used together with --staff-used-dep.", file=sys.stderr)
        return 2

    student_number = args.student_number
    student_name = args.student_name
    safe_student_name = sanitize_filename_component(student_name)
    safe_program_code = sanitize_filename_component(program_code)
    safe_date = args.start_date.strftime("%Y-%m-%d")

    pdf_filename = f"{student_number} {safe_student_name} {safe_program_code} TB.pdf"
    out_pdf = outdir / pdf_filename

    if os.name != "nt":
        print("ERROR: This workflow requires Windows + Excel + pywin32.", file=sys.stderr)
        return 2

    try:
        c4_val, d4_val, output_text, selected_sheet_name = fill_save_and_optionally_export_pdf(
            template_path=template_path,
            out_pdf=out_pdf,
            start_date=args.start_date,
            program_code=program_code,
            sai=args.sai,
            dep_ind=args.dep_ind,
            tas=args.tas,
            ind_override=args.ind_override,
            completer_program_code=args.completer_program_code,
            nostaff=args.nostaff,
            staff_used_ind=args.staff_used_ind,
            staff_used_dep=args.staff_used_dep,
            has_bs=args.has_bs,
            crossover_sai=args.crossover_sai,
            pell_used=args.pell_used,
            sheet_name=args.sheet,
            do_pdf=not args.no_pdf,
        )
    except KeyError as e:
        print(f"ERROR: Missing expected sheet: {e}", file=sys.stderr)
        return 2
    except LookupError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    print("Clean template used:")
    print(f"  {template_path}")
    print("Excel opened the template and generated the tuition breakdown PDF directly.")
    print("Wrote values on 'Program & Stafford Selection':")
    print(f"  B4 (Start Date): {args.start_date.strftime('%m/%d/%Y')}")
    print(f"  C4 (MASTER!E):   {c4_val}")
    print(f"  D4 (MASTER!F):   {d4_val}")
    print(f"  C43 (SAI):       {args.sai}")
    print(f"  N24 (TAS):       {'Yes' if args.tas else 'unchanged'}")
    print(f"  B43 (Has BS):    {'Yes' if args.has_bs else 'unchanged'}")
    print(
        f"  E43 (Crossover SAI): "
        f"{'unchanged' if args.crossover_sai is None else args.crossover_sai}"
    )
    print(
        f"  B49 (Pell Used): "
        f"{'unchanged' if args.pell_used is None else f'{args.pell_used:.3f}'}"
    )

    if args.nostaff:
        print("  D25 (Staff Used Dep): 31000.00")
        print("  E25 (Staff Used Ind): 57500.00")
    else:
        print(
            f"  D25 (Staff Used Dep): "
            f"{'unchanged' if args.staff_used_dep is None else f'{args.staff_used_dep:.2f}'}"
        )
        print(
            f"  E25 (Staff Used Ind): "
            f"{'unchanged' if args.staff_used_ind is None else f'{args.staff_used_ind:.2f}'}"
        )

    if args.dep_ind == "DEP":
        acyr_values = ["Dependent", "Dependent", "Dependent", "Dependent"]
        if args.ind_override is not None:
            start_index_map = {
                "ACYR1": 0,
                "ACYR2": 1,
                "ACYR3": 2,
                "ACYR4": 3,
            }
            for i in range(start_index_map[args.ind_override], 4):
                acyr_values[i] = "Independent"
    else:
        acyr_values = ["Independent", "Independent", "Independent", "Independent"]

    print(f"  G35 (ACYR1):     {acyr_values[0]}")
    print(f"  G36 (ACYR2):     {acyr_values[1]}")
    print(f"  G37 (ACYR3):     {acyr_values[2]}")
    print(f"  G38 (ACYR4):     {acyr_values[3]}")
    print(
        f"  PDF Sheet:       "
        f"{choose_breakdown_sheet(d4_val, args.sheet, args.completer_program_code)}"
    )
    if output_text:
        print("FA Breakdown Output:")
        print(output_text)

    if not args.no_pdf:
        print("PDF exported:")
        print(f"  {out_pdf}")
        try:
            if ask_open_pdf(out_pdf):
                open_pdf_in_adobe(out_pdf)
        except Exception as e:
            print(f"WARNING: PDF open failed: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
