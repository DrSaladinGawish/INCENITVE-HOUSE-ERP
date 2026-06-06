from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.ihe_models import Bank, BankTransaction
from app.schemas.bnk import BankCreate, BankUpdate, BankTransactionCreate


def get_banks(db: Session, skip: int = 0, limit: int = 100) -> list[Bank]:
    stmt = select(Bank).order_by(Bank.BankCode).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def get_bank(db: Session, bank_code: str) -> Bank | None:
    return db.get(Bank, bank_code)


def create_bank(db: Session, data: BankCreate) -> Bank:
    bank = Bank(**data.model_dump())
    db.add(bank)
    db.commit()
    db.refresh(bank)
    return bank


def update_bank(db: Session, bank_code: str, data: BankUpdate) -> Bank | None:
    bank = db.get(Bank, bank_code)
    if not bank:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(bank, key, val)
    db.commit()
    db.refresh(bank)
    return bank


def delete_bank(db: Session, bank_code: str) -> bool:
    bank = db.get(Bank, bank_code)
    if not bank:
        return False
    db.delete(bank)
    db.commit()
    return True


def get_bank_transactions(
    db: Session,
    bank_code: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[BankTransaction], int]:
    stmt = select(BankTransaction)
    count_stmt = select(func.count(BankTransaction.TransactionID))
    if bank_code:
        stmt = stmt.where(BankTransaction.BankCode == bank_code)
        count_stmt = count_stmt.where(BankTransaction.BankCode == bank_code)
    total = db.execute(count_stmt).scalar() or 0
    stmt = stmt.order_by(BankTransaction.TransactionDate.desc()).offset(skip).limit(limit)
    items = list(db.execute(stmt).scalars().all())
    return items, total


def create_bank_transaction(db: Session, data: BankTransactionCreate) -> BankTransaction:
    tx = BankTransaction(**data.model_dump())
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx
