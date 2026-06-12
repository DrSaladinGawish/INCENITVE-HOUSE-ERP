from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.fx_rate import FxRate
from app.models.ihe_models import Currency


def get_currencies(db: Session) -> list[Currency]:
    stmt = select(Currency).order_by(Currency.IsBaseCurrency.desc(), Currency.CurrencyCode)
    return list(db.execute(stmt).scalars().all())


def get_rate(db: Session, from_currency: str, to_currency: str, rate_date: date | None = None) -> Decimal | None:
    if from_currency == to_currency:
        return Decimal("1.0")
    target = rate_date or date.today()
    stmt = (
        select(FxRate.Rate)
        .where(
            FxRate.FromCurrency == from_currency,
            FxRate.ToCurrency == to_currency,
            FxRate.RateDate <= target,
        )
        .order_by(FxRate.RateDate.desc())
        .limit(1)
    )
    row = db.execute(stmt).scalar()
    if row is not None:
        return Decimal(str(row))
    return None


def convert_amount(
    db: Session, amount: Decimal, from_currency: str, to_currency: str, rate_date: date | None = None
) -> dict:
    if from_currency == to_currency:
        return {"amount": float(amount), "rate": 1.0, "from": from_currency, "to": to_currency}
    rate = get_rate(db, from_currency, to_currency, rate_date)
    if rate is None:
        inverted = get_rate(db, to_currency, from_currency, rate_date)
        if inverted is not None and inverted != 0:
            rate = Decimal("1.0") / inverted
    if rate is None:
        base_rate_1 = get_rate(db, from_currency, "EGP", rate_date)
        base_rate_2 = get_rate(db, to_currency, "EGP", rate_date)
        if base_rate_1 is not None and base_rate_2 is not None and base_rate_2 != 0:
            rate = base_rate_1 / base_rate_2
    if rate is None:
        return {"error": f"No rate found for {from_currency}→{to_currency}", "amount": None, "rate": None}
    converted = float(amount) * float(rate)
    return {"amount": round(converted, 2), "rate": round(float(rate), 6), "from": from_currency, "to": to_currency}


def get_rates_for_date(db: Session, rate_date: date) -> list[FxRate]:
    stmt = (
        select(FxRate)
        .where(FxRate.RateDate == rate_date)
        .order_by(FxRate.FromCurrency, FxRate.ToCurrency)
    )
    return list(db.execute(stmt).scalars().all())


def get_latest_rates(db: Session) -> list[dict]:
    currencies = get_currencies(db)
    base_currency = "EGP"
    results = []
    for c in currencies:
        code = c.CurrencyCode
        if code == base_currency:
            continue
        rate_val = get_rate(db, code, base_currency)
        if rate_val is not None:
            results.append({
                "currency": code, "name": c.CurrencyName, "symbol": c.Symbol,
                "rate_to_base": float(rate_val), "rate_date": date.today().isoformat(),
            })
    return results


def get_historical_rates(db: Session, currency: str, months: int = 6) -> list[dict]:
    from datetime import timedelta
    start = date.today() - timedelta(days=months * 30)
    stmt = (
        select(FxRate)
        .where(
            FxRate.FromCurrency == currency,
            FxRate.ToCurrency == "EGP",
            FxRate.RateDate >= start,
        )
        .order_by(FxRate.RateDate)
    )
    rows = db.execute(stmt).scalars().all()
    return [{"date": r.RateDate.isoformat(), "rate": float(r.Rate), "source": r.Source} for r in rows]


def add_rate(db: Session, rate_date: date, from_currency: str, to_currency: str, rate: float, source: str = "manual") -> FxRate:
    existing = db.execute(
        select(FxRate).where(
            FxRate.RateDate == rate_date,
            FxRate.FromCurrency == from_currency,
            FxRate.ToCurrency == to_currency,
        )
    ).scalar_one_or_none()
    if existing:
        existing.Rate = rate
        existing.Source = source
        db.flush()
        return existing
    fx = FxRate(
        RateDate=rate_date, FromCurrency=from_currency,
        ToCurrency=to_currency, Rate=rate, Source=source,
    )
    db.add(fx)
    db.flush()
    return fx


def calculate_gain_loss(
    db: Session, from_date: date, to_date: date
) -> dict:
    from app.models.ihe_models import BankTransaction, SalesInvoice, PurchaseVoucher

    results = {"gain_loss_items": [], "total_gain_loss": 0.0}

    for model, label, date_col, amount_col, currency_col in [
        (BankTransaction, "Bank", BankTransaction.TxnDate, BankTransaction.Amount, BankTransaction.CurrencyCode),
        (SalesInvoice, "Sales Invoice", SalesInvoice.InvoiceDate, SalesInvoice.TotalValue, SalesInvoice.CurrencyCode),
        (PurchaseVoucher, "Purchase", PurchaseVoucher.InvoiceDate, PurchaseVoucher.TotalValue, PurchaseVoucher.CurrencyCode),
    ]:
        stmt = select(model).where(date_col.between(from_date, to_date), currency_col.isnot(None))
        rows = db.execute(stmt).scalars().all()
        for row in rows:
            curr = getattr(row, currency_col.key)
            if not curr or curr == "EGP":
                continue
            amt = Decimal(str(getattr(row, amount_col.key) or 0))
            rate_at_date = get_rate(db, curr, "EGP", getattr(row, date_col.key))
            rate_now = get_rate(db, curr, "EGP")
            if not rate_at_date or not rate_now:
                continue
            egp_at_date = float(amt) * float(rate_at_date)
            egp_now = float(amt) * float(rate_now)
            diff = round(egp_now - egp_at_date, 2)
            results["gain_loss_items"].append({
                "type": label,
                "id": getattr(row, list(model.__table__.primary_key.columns.keys())[0]),
                "currency": curr,
                "original_amount": float(amt),
                "rate_at_transaction": float(rate_at_date),
                "rate_current": float(rate_now),
                "egp_at_transaction": round(egp_at_date, 2),
                "egp_current": round(egp_now, 2),
                "gain_loss": diff,
            })
            results["total_gain_loss"] = round(results["total_gain_loss"] + diff, 2)

    return results


def seed_default_rates(db: Session):
    today = date.today()
    defaults = [
        ("USD", "EGP", 49.25),
        ("EUR", "EGP", 52.80),
        ("GBP", "EGP", 61.50),
    ]
    for from_c, to_c, rate in defaults:
        existing = db.execute(
            select(FxRate).where(FxRate.RateDate == today, FxRate.FromCurrency == from_c, FxRate.ToCurrency == to_c)
        ).scalar_one_or_none()
        if not existing:
            db.add(FxRate(RateDate=today, FromCurrency=from_c, ToCurrency=to_c, Rate=rate, Source="seed"))
    db.commit()
