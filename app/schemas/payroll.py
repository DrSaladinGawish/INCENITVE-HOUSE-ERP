from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


# --- SalaryStructure ---
class SalaryStructureBase(BaseModel):
    EmployeeCode: str = Field(..., max_length=10)
    BasicSalary: Optional[float] = None
    HousingAllowance: Optional[float] = None
    TransportationAllowance: Optional[float] = None
    OtherAllowances: Optional[float] = None
    Deductions: Optional[float] = None
    EffectiveFrom: date
    EffectiveTo: Optional[date] = None
    IsActive: Optional[bool] = True


class SalaryStructureCreate(SalaryStructureBase):
    pass


class SalaryStructureUpdate(BaseModel):
    BasicSalary: Optional[float] = None
    HousingAllowance: Optional[float] = None
    TransportationAllowance: Optional[float] = None
    OtherAllowances: Optional[float] = None
    Deductions: Optional[float] = None
    EffectiveFrom: Optional[date] = None
    EffectiveTo: Optional[date] = None
    IsActive: Optional[bool] = None


class SalaryStructureResponse(SalaryStructureBase):
    SalaryStructureID: int
    CreatedAt: datetime

    class Config:
        from_attributes = True


# --- Allowance ---
class AllowanceBase(BaseModel):
    AllowanceType: str = Field(..., max_length=100)
    Amount: float = 0
    Description: Optional[str] = None


class AllowanceCreate(AllowanceBase):
    pass


class AllowanceResponse(AllowanceBase):
    AllowanceID: int
    PaySlipID: int

    class Config:
        from_attributes = True


# --- Deduction ---
class DeductionBase(BaseModel):
    DeductionType: str = Field(..., max_length=100)
    Amount: float = 0
    Description: Optional[str] = None


class DeductionCreate(DeductionBase):
    pass


class DeductionResponse(DeductionBase):
    DeductionID: int
    PaySlipID: int

    class Config:
        from_attributes = True


# --- PaySlip ---
class PaySlipBase(BaseModel):
    EmployeeCode: str = Field(..., max_length=10)
    PayPeriod: str = Field(..., max_length=20)
    PayDate: date
    Remarks: Optional[str] = None


class PaySlipCreate(PaySlipBase):
    allowances: list[AllowanceCreate] = []
    deductions: list[DeductionCreate] = []


class PaySlipUpdate(BaseModel):
    Status: Optional[str] = None
    Remarks: Optional[str] = None


class PaySlipResponse(PaySlipBase):
    PaySlipID: int
    BasicSalary: float
    TotalAllowances: float
    GrossPay: float
    TotalDeductions: float
    NetPay: float
    Status: str
    CreatedAt: datetime
    allowances: list[AllowanceResponse] = []
    deductions: list[DeductionResponse] = []

    class Config:
        from_attributes = True


class PaySlipList(BaseModel):
    items: list[PaySlipResponse]
    total: int
    page: int = 1
    page_size: int = 50


# --- Attendance ---
class AttendanceBase(BaseModel):
    EmployeeCode: str = Field(..., max_length=10)
    AttendanceDate: date
    CheckIn: Optional[datetime] = None
    CheckOut: Optional[datetime] = None
    HoursWorked: Optional[float] = None
    Status: str = "present"
    Remarks: Optional[str] = None


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceUpdate(BaseModel):
    CheckIn: Optional[datetime] = None
    CheckOut: Optional[datetime] = None
    HoursWorked: Optional[float] = None
    Status: Optional[str] = None
    Remarks: Optional[str] = None


class AttendanceResponse(AttendanceBase):
    AttendanceID: int

    class Config:
        from_attributes = True


# --- Payroll Run ---
class PayrollRunRequest(BaseModel):
    PayPeriod: str = Field(..., max_length=20)
    PayDate: date
    EmployeeCodes: list[str] = []


class PayrollRunResponse(BaseModel):
    processed: int
    total_gross: float
    total_deductions: float
    total_net: float
