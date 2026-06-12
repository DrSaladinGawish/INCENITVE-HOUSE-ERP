from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import bnk_service
from app.schemas.bnk import (
    BankCreate, BankUpdate, BankResponse,
    BankTransactionCreate, BankTransactionUpdate, BankTransactionResponse, BankTransactionList,
)

router = APIRouter(prefix="/api/bnk", tags=["Banking"])


@router.get("/banks", response_model=list[BankResponse])
def list_banks(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    return bnk_service.get_banks(db, skip=skip, limit=limit)


@router.get("/banks/{bank_code}", response_model=BankResponse)
def get_bank(bank_code: str, db: Session = Depends(get_db)):
    bank = bnk_service.get_bank(db, bank_code)
    if not bank:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found")
    return bank


@router.post("/banks", response_model=BankResponse, status_code=status.HTTP_201_CREATED)
def create_bank(data: BankCreate, db: Session = Depends(get_db)):
    return bnk_service.create_bank(db, data)


@router.put("/banks/{bank_code}", response_model=BankResponse)
def update_bank(bank_code: str, data: BankUpdate, db: Session = Depends(get_db)):
    bank = bnk_service.update_bank(db, bank_code, data)
    if not bank:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found")
    return bank


@router.delete("/banks/{bank_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bank(bank_code: str, db: Session = Depends(get_db)):
    if not bnk_service.delete_bank(db, bank_code):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found")


@router.get("/transactions", response_model=BankTransactionList)
def list_transactions(
    bank_code: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    items, total = bnk_service.get_bank_transactions(db, bank_code=bank_code, skip=skip, limit=page_size)
    return BankTransactionList(items=items, total=total, page=page, page_size=page_size)


@router.post("/transactions", response_model=BankTransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(data: BankTransactionCreate, db: Session = Depends(get_db)):
    return bnk_service.create_bank_transaction(db, data)


@router.get("/transactions/{transaction_id}", response_model=BankTransactionResponse)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    tx = bnk_service.get_bank_transaction(db, transaction_id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return tx


@router.put("/transactions/{transaction_id}", response_model=BankTransactionResponse)
def update_transaction(transaction_id: int, data: BankTransactionUpdate, db: Session = Depends(get_db)):
    tx = bnk_service.update_bank_transaction(db, transaction_id, data)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return tx


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    if not bnk_service.delete_bank_transaction(db, transaction_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
