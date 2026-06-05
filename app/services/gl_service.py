from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.models.ihe_models import ChartOfAccounts, JournalVoucher, JournalVoucherLine, Employee
from app.schemas.gl import JournalVoucherCreate, EmployeeCreate, EmployeeUpdate


def get_accounts(db: Session, account_type: str | None = None) -> list[ChartOfAccounts]:
    stmt = select(ChartOfAccounts)
    if account_type:
        stmt = stmt.where(ChartOfAccounts.AccountType == account_type)
    return list(db.execute(stmt).scalars().all())


def get_account(db: Session, account_code: str) -> ChartOfAccounts | None:
    return db.get(ChartOfAccounts, account_code)


def get_journal_vouchers(
    db: Session,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[JournalVoucher], int]:
    stmt = select(JournalVoucher).options(joinedload(JournalVoucher.lines))
    total = db.execute(select(func.count(JournalVoucher.JVNumber))).scalar() or 0
    stmt = stmt.order_by(JournalVoucher.JVDate.desc()).offset(skip).limit(limit)
    items = list(db.execute(stmt).scalars().unique().all())
    return items, total


def get_journal_voucher(db: Session, jv_number: str) -> JournalVoucher | None:
    stmt = select(JournalVoucher).where(JournalVoucher.JVNumber == jv_number).options(joinedload(JournalVoucher.lines))
    return db.execute(stmt).unique().scalar_one_or_none()


def create_journal_voucher(db: Session, data: JournalVoucherCreate) -> JournalVoucher:
    lines_data = data.lines
    jv_data = data.model_dump(exclude={"lines"})
    jv = JournalVoucher(**jv_data)
    db.add(jv)
    db.flush()
    for line_data in lines_data:
        line = JournalVoucherLine(JVNumber=jv.JVNumber, **line_data.model_dump())
        db.add(line)
    db.commit()
    db.refresh(jv)
    return jv


def get_employees(db: Session, skip: int = 0, limit: int = 100) -> list[Employee]:
    stmt = select(Employee).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def get_employee(db: Session, emp_code: str) -> Employee | None:
    return db.get(Employee, emp_code)


def create_employee(db: Session, data: EmployeeCreate) -> Employee:
    emp = Employee(**data.model_dump())
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


def update_employee(db: Session, emp_code: str, data: EmployeeUpdate) -> Employee | None:
    emp = db.get(Employee, emp_code)
    if not emp:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(emp, key, val)
    db.commit()
    db.refresh(emp)
    return emp


def delete_employee(db: Session, emp_code: str) -> bool:
    emp = db.get(Employee, emp_code)
    if not emp:
        return False
    db.delete(emp)
    db.commit()
    return True
