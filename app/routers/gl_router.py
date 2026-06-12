from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import gl_service
from app.schemas.gl import (
    ChartOfAccountsResponse, JournalVoucherCreate, JournalVoucherUpdate, JournalVoucherResponse, JournalVoucherList,
    EmployeeCreate, EmployeeUpdate, EmployeeResponse,
)

router = APIRouter(prefix="/api/gl", tags=["General Ledger"])


@router.get("/accounts", response_model=list[ChartOfAccountsResponse])
def list_accounts(account_type: str | None = Query(None), db: Session = Depends(get_db)):
    return gl_service.get_accounts(db, account_type=account_type)


@router.get("/accounts/{account_code}", response_model=ChartOfAccountsResponse)
def get_account(account_code: str, db: Session = Depends(get_db)):
    account = gl_service.get_account(db, account_code)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


@router.get("/vouchers", response_model=JournalVoucherList)
def list_vouchers(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    items, total = gl_service.get_journal_vouchers(db, skip=skip, limit=page_size)
    return JournalVoucherList(items=items, total=total, page=page, page_size=page_size)


@router.get("/vouchers/{jv_number}", response_model=JournalVoucherResponse)
def get_voucher(jv_number: str, db: Session = Depends(get_db)):
    jv = gl_service.get_journal_voucher(db, jv_number)
    if not jv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal voucher not found")
    return jv


@router.post("/vouchers", response_model=JournalVoucherResponse, status_code=status.HTTP_201_CREATED)
def create_voucher(data: JournalVoucherCreate, db: Session = Depends(get_db)):
    return gl_service.create_journal_voucher(db, data)


@router.put("/vouchers/{jv_number}", response_model=JournalVoucherResponse)
def update_jv(jv_number: str, data: JournalVoucherUpdate, db: Session = Depends(get_db)):
    jv = gl_service.update_journal_voucher(db, jv_number, data)
    if not jv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal voucher not found")
    return jv


@router.delete("/vouchers/{jv_number}", status_code=status.HTTP_204_NO_CONTENT)
def delete_jv(jv_number: str, db: Session = Depends(get_db)):
    if not gl_service.delete_journal_voucher(db, jv_number):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal voucher not found")


@router.get("/employees", response_model=list[EmployeeResponse])
def list_employees(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    return gl_service.get_employees(db, skip=skip, limit=limit)


@router.get("/employees/{emp_code}", response_model=EmployeeResponse)
def get_employee(emp_code: str, db: Session = Depends(get_db)):
    emp = gl_service.get_employee(db, emp_code)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return emp


@router.post("/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(data: EmployeeCreate, db: Session = Depends(get_db)):
    return gl_service.create_employee(db, data)


@router.put("/employees/{emp_code}", response_model=EmployeeResponse)
def update_employee(emp_code: str, data: EmployeeUpdate, db: Session = Depends(get_db)):
    emp = gl_service.update_employee(db, emp_code, data)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return emp


@router.delete("/employees/{emp_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(emp_code: str, db: Session = Depends(get_db)):
    if not gl_service.delete_employee(db, emp_code):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
