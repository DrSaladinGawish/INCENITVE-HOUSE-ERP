from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import fx_service

router = APIRouter(prefix="/api/fx", tags=["Foreign Exchange"])


@router.get("/currencies")
def list_currencies(db: Session = Depends(get_db)):
    currencies = fx_service.get_currencies(db)
    return [
        {
            "code": c.CurrencyCode,
            "name": c.CurrencyName,
            "symbol": c.Symbol,
            "is_base": c.IsBaseCurrency,
        }
        for c in currencies
    ]


@router.get("/rates")
def get_rates(rate_date: date | None = Query(None), db: Session = Depends(get_db)):
    if rate_date:
        rates = fx_service.get_rates_for_date(db, rate_date)
    else:
        rates_by_curr = fx_service.get_latest_rates(db)
        return {"rates": rates_by_curr, "base_currency": "EGP", "rate_date": date.today().isoformat()}
    return {
        "rates": [
            {
                "id": r.RateID,
                "date": r.RateDate.isoformat(),
                "from": r.FromCurrency,
                "to": r.ToCurrency,
                "rate": float(r.Rate),
                "source": r.Source,
            }
            for r in rates
        ],
        "rate_date": rate_date.isoformat(),
    }


@router.post("/rates")
def add_rate(
    rate_date: date = Query(...),
    from_currency: str = Query(...),
    to_currency: str = Query(...),
    rate: float = Query(...),
    source: str = Query("manual"),
    db: Session = Depends(get_db),
):
    if rate <= 0:
        raise HTTPException(status_code=400, detail="Rate must be positive")
    fx = fx_service.add_rate(db, rate_date, from_currency.upper(), to_currency.upper(), rate, source)
    return {
        "id": fx.RateID,
        "date": fx.RateDate.isoformat(),
        "from": fx.FromCurrency,
        "to": fx.ToCurrency,
        "rate": float(fx.Rate),
        "source": fx.Source,
    }


@router.post("/rates/seed")
def seed_rates(db: Session = Depends(get_db)):
    fx_service.seed_default_rates(db)
    return {"detail": "Default rates seeded for today"}


@router.get("/convert")
def convert(
    amount: float = Query(...),
    from_currency: str = Query(...),
    to_currency: str = Query(...),
    rate_date: date | None = Query(None),
    db: Session = Depends(get_db),
):
    result = fx_service.convert_amount(db, Decimal(str(amount)), from_currency.upper(), to_currency.upper(), rate_date)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/gain-loss")
def gain_loss(
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db),
):
    return fx_service.calculate_gain_loss(db, from_date, to_date)


@router.get("/historical")
def historical(
    currency: str = Query(...),
    months: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db),
):
    return {"currency": currency.upper(), "rates": fx_service.get_historical_rates(db, currency.upper(), months)}
