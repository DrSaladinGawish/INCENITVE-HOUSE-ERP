from datetime import date
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.models.payroll import SalaryStructure, PaySlip, Allowance, Deduction, Attendance
from app.schemas.payroll import (
    SalaryStructureCreate, SalaryStructureUpdate,
    PaySlipCreate, PaySlipUpdate,
    AttendanceCreate, AttendanceUpdate,
    PayrollRunRequest,
)


# --- SalaryStructure ---
def get_salary_structures(db: Session, skip: int = 0, limit: int = 100) -> list[SalaryStructure]:
    stmt = select(SalaryStructure).order_by(SalaryStructure.SalaryStructureID.desc()).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def get_salary_structure(db: Session, structure_id: int) -> SalaryStructure | None:
    return db.get(SalaryStructure, structure_id)


def get_active_structure(db: Session, employee_code: str) -> SalaryStructure | None:
    stmt = (
        select(SalaryStructure)
        .where(SalaryStructure.EmployeeCode == employee_code)
        .where(SalaryStructure.IsActive == True)
        .order_by(SalaryStructure.EffectiveFrom.desc())
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def create_salary_structure(db: Session, data: SalaryStructureCreate) -> SalaryStructure:
    obj = SalaryStructure(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_salary_structure(db: Session, structure_id: int, data: SalaryStructureUpdate) -> SalaryStructure | None:
    obj = db.get(SalaryStructure, structure_id)
    if not obj:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, val)
    db.commit()
    db.refresh(obj)
    return obj


def delete_salary_structure(db: Session, structure_id: int) -> bool:
    obj = db.get(SalaryStructure, structure_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


# --- PaySlip ---
def get_payslips(
    db: Session,
    employee_code: str | None = None,
    pay_period: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[PaySlip], int]:
    stmt = select(PaySlip).options(joinedload(PaySlip.allowances), joinedload(PaySlip.deductions))
    count_stmt = select(func.count(PaySlip.PaySlipID))
    if employee_code:
        stmt = stmt.where(PaySlip.EmployeeCode == employee_code)
        count_stmt = count_stmt.where(PaySlip.EmployeeCode == employee_code)
    if pay_period:
        stmt = stmt.where(PaySlip.PayPeriod == pay_period)
        count_stmt = count_stmt.where(PaySlip.PayPeriod == pay_period)
    total = db.execute(count_stmt).scalar() or 0
    stmt = stmt.order_by(PaySlip.PayDate.desc()).offset(skip).limit(limit)
    items = list(db.execute(stmt).scalars().unique().all())
    return items, total


def get_payslip(db: Session, payslip_id: int) -> PaySlip | None:
    stmt = (
        select(PaySlip)
        .where(PaySlip.PaySlipID == payslip_id)
        .options(joinedload(PaySlip.allowances), joinedload(PaySlip.deductions))
    )
    return db.execute(stmt).unique().scalar_one_or_none()


def create_payslip(db: Session, data: PaySlipCreate) -> PaySlip:
    allowances_data = data.allowances
    deductions_data = data.deductions
    slip_data = data.model_dump(exclude={"allowances", "deductions"})
    payslip = PaySlip(**slip_data)
    db.add(payslip)
    db.flush()
    for a in allowances_data:
        db.add(Allowance(PaySlipID=payslip.PaySlipID, **a.model_dump()))
    for d in deductions_data:
        db.add(Deduction(PaySlipID=payslip.PaySlipID, **d.model_dump()))
    db.commit()
    db.refresh(payslip)
    return payslip


def update_payslip(db: Session, payslip_id: int, data: PaySlipUpdate) -> PaySlip | None:
    obj = db.get(PaySlip, payslip_id)
    if not obj:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, val)
    db.commit()
    db.refresh(obj)
    return obj


def delete_payslip(db: Session, payslip_id: int) -> bool:
    obj = db.get(PaySlip, payslip_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


# --- Attendance ---
def get_attendance_records(
    db: Session,
    employee_code: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Attendance], int]:
    stmt = select(Attendance)
    count_stmt = select(func.count(Attendance.AttendanceID))
    if employee_code:
        stmt = stmt.where(Attendance.EmployeeCode == employee_code)
        count_stmt = count_stmt.where(Attendance.EmployeeCode == employee_code)
    if from_date:
        stmt = stmt.where(Attendance.AttendanceDate >= from_date)
        count_stmt = count_stmt.where(Attendance.AttendanceDate >= from_date)
    if to_date:
        stmt = stmt.where(Attendance.AttendanceDate <= to_date)
        count_stmt = count_stmt.where(Attendance.AttendanceDate <= to_date)
    total = db.execute(count_stmt).scalar() or 0
    stmt = stmt.order_by(Attendance.AttendanceDate.desc()).offset(skip).limit(limit)
    items = list(db.execute(stmt).scalars().all())
    return items, total


def create_attendance(db: Session, data: AttendanceCreate) -> Attendance:
    obj = Attendance(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_attendance(db: Session, attendance_id: int, data: AttendanceUpdate) -> Attendance | None:
    obj = db.get(Attendance, attendance_id)
    if not obj:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, val)
    db.commit()
    db.refresh(obj)
    return obj


def delete_attendance(db: Session, attendance_id: int) -> bool:
    obj = db.get(Attendance, attendance_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


# --- Payroll Run / Calculate ---
def calculate_salary(db: Session, employee_code: str, pay_period: str, pay_date: date) -> dict:
    structure = get_active_structure(db, employee_code)
    basic = float(structure.BasicSalary) if structure else 0.0
    housing = float(structure.HousingAllowance) if structure else 0.0
    transport = float(structure.TransportationAllowance) if structure else 0.0
    other = float(structure.OtherAllowances) if structure else 0.0
    total_allowances = housing + transport + other
    gross = basic + total_allowances
    struct_ded = float(structure.Deductions) if structure else 0.0

    days_parts = pay_period.split("-")
    if len(days_parts) >= 2:
        try:
            year, month = int(days_parts[0]), int(days_parts[1])
        except ValueError:
            year, month = pay_date.year, pay_date.month
    else:
        year, month = pay_date.year, pay_date.month
    from calendar import monthrange
    total_work_days = monthrange(year, month)[1]

    from sqlalchemy import func as sa_func
    stmt = (
        select(sa_func.count(Attendance.AttendanceID))
        .where(Attendance.EmployeeCode == employee_code)
        .where(sa_func.extract("year", Attendance.AttendanceDate) == year)
        .where(sa_func.extract("month", Attendance.AttendanceDate) == month)
        .where(Attendance.Status == "present")
    )
    present_days = db.execute(stmt).scalar() or 0
    absent_days = total_work_days - present_days
    if absent_days < 0:
        absent_days = 0

    daily_rate = gross / total_work_days if total_work_days else 0
    absent_deduction = daily_rate * absent_days
    total_deductions = struct_ded + absent_deduction
    net = gross - total_deductions
    if net < 0:
        net = 0

    return {
        "employee_code": employee_code,
        "pay_period": pay_period,
        "pay_date": pay_date,
        "basic_salary": round(basic, 2),
        "total_allowances": round(total_allowances, 2),
        "gross_pay": round(gross, 2),
        "total_deductions": round(total_deductions, 2),
        "net_pay": round(net, 2),
        "present_days": present_days,
        "absent_days": absent_days,
        "status": "calculated",
    }


def run_payroll(db: Session, req: PayrollRunRequest) -> dict:
    processed = 0
    total_gross = 0.0
    total_deductions = 0.0
    total_net = 0.0
    for emp_code in req.EmployeeCodes:
        result = calculate_salary(db, emp_code, req.PayPeriod, req.PayDate)
        payslip = PaySlip(
            EmployeeCode=emp_code,
            PayPeriod=req.PayPeriod,
            PayDate=req.PayDate,
            BasicSalary=result["basic_salary"],
            TotalAllowances=result["total_allowances"],
            GrossPay=result["gross_pay"],
            TotalDeductions=result["total_deductions"],
            NetPay=result["net_pay"],
            Status="processed",
        )
        db.add(payslip)
        db.flush()
        processed += 1
        total_gross += result["gross_pay"]
        total_deductions += result["total_deductions"]
        total_net += result["net_pay"]
    db.commit()
    return {
        "processed": processed,
        "total_gross": round(total_gross, 2),
        "total_deductions": round(total_deductions, 2),
        "total_net": round(total_net, 2),
    }
