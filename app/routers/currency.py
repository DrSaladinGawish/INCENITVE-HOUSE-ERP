import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.models import CurrencyRate, AuditTrail

router = APIRouter(prefix="/api/v1/currency", tags=["currency"])


@router.get("/rates")
async def list_rates(currency: str = "", date: str = "", limit: int = 100, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    q = select(CurrencyRate).order_by(CurrencyRate.rate_date.desc(), CurrencyRate.currency_code)
    if currency: q = q.where(CurrencyRate.currency_code == currency.upper())
    if date: q = q.where(CurrencyRate.rate_date == date)
    q = q.limit(limit)
    result = await db.execute(q)
    return [{"id": r.rate_id, "currency": r.currency_code, "rate": r.rate_to_egp, "date": str(r.rate_date)} for r in result.all()]


@router.get("/convert")
async def convert_currency(amount: float = 0, from_currency: str = "USD", to_currency: str = "EGP", date: str = "", db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    if from_currency == to_currency: return {"amount": amount, "from": from_currency, "to": to_currency, "converted": amount, "rate": 1.0}
    q = select(CurrencyRate).where(CurrencyRate.currency_code == from_currency.upper())
    if date: q = q.where(CurrencyRate.rate_date == date)
    else: q = q.order_by(CurrencyRate.rate_date.desc())
    q = q.limit(1)
    result = await db.execute(q)
    row = result.scalar_one_or_none()
    rate = row.rate_to_egp if row else 0.0
    if rate == 0: raise HTTPException(status_code=404, detail=f"No rate for {from_currency}")
    if to_currency != "EGP": raise HTTPException(status_code=400, detail="Only EGP target supported")
    return {"amount": amount, "from": from_currency, "to": to_currency, "converted": round(amount * rate, 2), "rate": rate, "date": str(row.rate_date) if row else None}


@router.post("/rates")
async def set_rate(currency_code: str, rate_to_egp: float, rate_date: str = "", db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    date_val = rate_date or str(datetime.date.today())
    r = CurrencyRate(currency_code=currency_code.upper(), rate_to_egp=rate_to_egp, rate_date=datetime.datetime.strptime(date_val, "%Y-%m-%d").date())
    db.add(r)
    db.add(AuditTrail(table_name="currency_rates", record_id=0, action="SET_RATE", new_values={"currency": currency_code, "rate": rate_to_egp, "date": date_val}, changed_by=user["username"], changed_at=datetime.datetime.utcnow()))
    await db.commit(); await db.refresh(r)
    return {"id": r.rate_id, "currency": r.currency_code, "rate": r.rate_to_egp, "date": str(r.rate_date)}
