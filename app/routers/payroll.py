from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import payroll_service
from app.schemas.payroll import (
    SalaryStructureCreate, SalaryStructureUpdate, SalaryStructureResponse,
    PaySlipCreate, PaySlipUpdate, PaySlipResponse, PaySlipList,
    AllowanceCreate, AllowanceResponse,
    DeductionCreate, DeductionResponse,
    AttendanceCreate, AttendanceUpdate, AttendanceResponse,
    PayrollRunRequest, PayrollRunResponse,
)

router = APIRouter(prefix="/api/payroll", tags=["Payroll"])


# --- Salary Structure ---
@router.get("/structures", response_model=list[SalaryStructureResponse])
def list_structures(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    return payroll_service.get_salary_structures(db, skip=skip, limit=limit)


@router.get("/structures/{structure_id}", response_model=SalaryStructureResponse)
def get_structure(structure_id: int, db: Session = Depends(get_db)):
    obj = payroll_service.get_salary_structure(db, structure_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary structure not found")
    return obj


@router.post("/structures", response_model=SalaryStructureResponse, status_code=status.HTTP_201_CREATED)
def create_structure(data: SalaryStructureCreate, db: Session = Depends(get_db)):
    return payroll_service.create_salary_structure(db, data)


@router.put("/structures/{structure_id}", response_model=SalaryStructureResponse)
def update_structure(structure_id: int, data: SalaryStructureUpdate, db: Session = Depends(get_db)):
    obj = payroll_service.update_salary_structure(db, structure_id, data)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary structure not found")
    return obj


@router.delete("/structures/{structure_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_structure(structure_id: int, db: Session = Depends(get_db)):
    if not payroll_service.delete_salary_structure(db, structure_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary structure not found")


# --- PaySlip ---
@router.get("/payslips", response_model=PaySlipList)
def list_payslips(
    employee_code: str | None = Query(None),
    pay_period: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    items, total = payroll_service.get_payslips(db, employee_code=employee_code, pay_period=pay_period, skip=skip, limit=page_size)
    return PaySlipList(items=items, total=total, page=page, page_size=page_size)


@router.get("/payslips/{payslip_id}", response_model=PaySlipResponse)
def get_payslip(payslip_id: int, db: Session = Depends(get_db)):
    obj = payroll_service.get_payslip(db, payslip_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payslip not found")
    return obj


@router.post("/payslips", response_model=PaySlipResponse, status_code=status.HTTP_201_CREATED)
def create_payslip(data: PaySlipCreate, db: Session = Depends(get_db)):
    return payroll_service.create_payslip(db, data)


@router.put("/payslips/{payslip_id}", response_model=PaySlipResponse)
def update_payslip(payslip_id: int, data: PaySlipUpdate, db: Session = Depends(get_db)):
    obj = payroll_service.update_payslip(db, payslip_id, data)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payslip not found")
    return obj


@router.delete("/payslips/{payslip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payslip(payslip_id: int, db: Session = Depends(get_db)):
    if not payroll_service.delete_payslip(db, payslip_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payslip not found")


# --- Attendance ---
@router.get("/attendance", response_model=list[AttendanceResponse])
def list_attendance(
    employee_code: str | None = Query(None),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    items, _ = payroll_service.get_attendance_records(db, employee_code=employee_code, from_date=from_date, to_date=to_date, skip=skip, limit=limit)
    return items


@router.post("/attendance", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def create_attendance(data: AttendanceCreate, db: Session = Depends(get_db)):
    return payroll_service.create_attendance(db, data)


@router.put("/attendance/{attendance_id}", response_model=AttendanceResponse)
def update_attendance(attendance_id: int, data: AttendanceUpdate, db: Session = Depends(get_db)):
    obj = payroll_service.update_attendance(db, attendance_id, data)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")
    return obj


@router.delete("/attendance/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendance(attendance_id: int, db: Session = Depends(get_db)):
    if not payroll_service.delete_attendance(db, attendance_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")


# --- Calculate / Run Payroll ---
@router.post("/calculate")
def calculate_salary(employee_code: str, pay_period: str, pay_date: date, db: Session = Depends(get_db)):
    return payroll_service.calculate_salary(db, employee_code, pay_period, pay_date)


@router.post("/run", response_model=PayrollRunResponse)
def run_payroll(req: PayrollRunRequest, db: Session = Depends(get_db)):
    return payroll_service.run_payroll(db, req)
