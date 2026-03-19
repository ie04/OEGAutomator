from typing import Protocol, Optional, List
from dataclasses import dataclass, field
from datetime import date
from automations.playwright.util.timestamp import get_timestamp
from decimal import Decimal
from enum import Enum

@dataclass
class StudentSnapshot:
    student_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[date] = None
    ssn: Optional[str] = None
    enrollment_version_code: Optional[str] = None
    program_start_date: Optional[date] = None
    is_dependent: bool = False
    email: Optional[str] = None

class RedFlagCode(Enum):
    DUAL_ENROLLMENT_FT = "DUAL_ENROLLMENT_FT"
    DUAL_ENROLLMENT_NRF = "DUAL_ENROLLMENT_NRF"
    DUAL_ENROLLMENT_TQT = "DUAL_ENROLLMENT_TQT"
    DUAL_ENROLLMENT_HT = "DUAL_ENROLLMENT_HT"
    AGG_LIMIT_ACYR1 = "AGG_LIMIT_ACYR1"
    AGG_LIMIT_ACYR2 = "AGG_LIMIT_ACYR2"
    AGG_LIMIT_ACYR3 = "AGG_LIMIT_ACYR3"
    AGG_LIMIT_ACYR4 = "AGG_LIMIT_ACYR4"

@dataclass
class RedFlag:
    code: RedFlagCode
    message: str

class RFLoanStatus(str, Enum):
    DELINQUENT = "delinquent"
    DEFAULT = "default"
    TPD = "total_permanent_discharge"

class RFEnrollmentStatus(str,Enum):
    NRF = "NRF"
    LHT = "LHT"
    HT = "HT"
    TQT = "TQT"
    FT = "FT"
    G = "G"

@dataclass(slots=True)
class RFEnrollment:
    school_name: str
    status: RFEnrollmentStatus

    def __post_init__(self) -> None:
        if not self.school_name.strip():
            raise ValueError("school_name cannot be blank")

@dataclass(slots=True)
class RFLoan:
    loan_amount: Decimal
    servicer_name: str
    servicer_phone: str
    rf_status: RFLoanStatus
    rf_status_date: date
    days_delinquent: int | None = None

    def __post_init__(self) -> None:
        if self.loan_amount < 0:
            raise ValueError("loan_amount cannot be negative")

        if not self.servicer_name.strip():
            raise ValueError("servicer_name cannot be blank")

        if not self.servicer_phone.strip():
            raise ValueError("servicer_phone cannot be blank")

        if self.rf_status == RFLoanStatus.DELINQUENT:
            if self.days_delinquent is None:
                raise ValueError(
                    "days_delinquent is required when rf_status is DELINQUENT"
                )
            if self.days_delinquent < 0:
                raise ValueError("days_delinquent cannot be negative")
        else:
            if self.days_delinquent is not None:
                raise ValueError(
                    "days_delinquent must be None unless rf_status is DELINQUENT"
                )

@dataclass(slots=True)
class NSLDSSnapshot:
    sub_stafford_amount: int = 0
    total_stafford_amount: int = 0
    pell_leu: float = 0.0
    rf_enrollments: List[RFEnrollment] = field(default_factory=list)
    rf_loans: List[RFLoan] = field(default_factory=list)

@dataclass
class AuditSnapshot:
    has_fa_history: bool = False
    sub_stafford_amount: float = 0.0
    total_stafford_amount: float = 0.0 
    pell_leu: str = ""
    has_agg_limit: bool = False
    has_dep_unsub: bool = False
    has_dual_enrollment: bool = False
    has_pending_disb: bool = False
    has_olp: bool = False
    red_flags: List[RedFlag] = field(default_factory=list)

    def __str__(self):
        return (
          f"FA History: {'Y' if self.has_fa_history else 'N'}\n"
          f"Pell LEU Used: {self.pell_leu} (has 1st BS - Y/N)\n"  
          f"Sub Staff amt Used: ${self.sub_stafford_amount}\n"
          f"Total Staff Amt Used: ${self.total_stafford_amount}\n"
          f"Aggregate Limits: {'Y' if self.has_agg_limit else 'N'}\n"
          f"Dep only Add’l Unsub: {'Y' if self.has_dep_unsub else 'N'}\n"
          f"Dual Enrollment: {'Y' if self.has_dual_enrollment else 'N'}\n"
          f"Pending Disbursements: {'Y' if self.has_pending_disb else 'N'}\n"
          f"OLP Date: {'Y' if self.has_olp else 'N'}\n"
          f"{get_timestamp()}"
          
        )
    
    def append_red_flag(self, code: RedFlagCode, message: str = ""):
        match code:
            case RedFlagCode.DUAL_ENROLLMENT_NRF:
                self.red_flags.append(RedFlag(code, f"Uncounseled on NRF w/ {message}\n"))

            case RedFlagCode.DUAL_ENROLLMENT_FT:
                self.red_flags.append(RedFlag(code, f"Uncounseled on FT w/ {message}\n"))

            case RedFlagCode.DUAL_ENROLLMENT_TQT:
                self.red_flags.append(RedFlag(code, f"Uncounseled on TQT w/ {message}\n"))

            case RedFlagCode.DUAL_ENROLLMENT_HT:
                self.red_flags.append(RedFlag(code,f"Uncounseled on HT w/ {message}\n"))

            case RedFlagCode.AGG_LIMIT_ACYR1:
                self.red_flags.append(RedFlag(code, f"Uncounseled on 1st ACYR agg limit\n"))

            case RedFlagCode.AGG_LIMIT_ACYR2:
                self.red_flags.append(RedFlag(code, f"Uncounseled on 2nd ACYR agg limit\n"))
            
            case RedFlagCode.AGG_LIMIT_ACYR3:
                self.red_flags.append(RedFlag(code, f"Uncounseled on 3rd ACYR agg limit\n"))
            
            case RedFlagCode.AGG_LIMIT_ACYR4:
                self.red_flags.append(RedFlag(code, f"Uncounseled on 4th ACYR agg limit\n"))



class SalesforcePort(Protocol):
    async def fetch_student_snapshot(self, student_id: str) -> StudentSnapshot: ...

class NSLDSPort(Protocol):
    async def fetch_NSLDS_snapshot(self, student: StudentSnapshot) -> NSLDSSnapshot: ...
