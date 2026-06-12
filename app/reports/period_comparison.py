from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app.services import financial_reports_service as frs


def _resolve_period(period: str) -> tuple[date | None, date | None]:
    today = date.today()
    period = period.lower()

    if period in ("this_month", "current_month"):
        return (today.replace(day=1), today)

    if period == "last_month":
        first = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        last = today.replace(day=1) - timedelta(days=1)
        return (first, last)

    if period in ("this_quarter", "current_quarter"):
        q_start = ((today.month - 1) // 3) * 3 + 1
        return (today.replace(month=q_start, day=1), today)

    if period == "last_quarter":
        q = ((today.month - 1) // 3)
        if q == 0:
            q_start = 10
            year = today.year - 1
        else:
            q_start = ((q - 1) * 3) + 1
            year = today.year
        q_start_date = today.replace(year=year, month=q_start, day=1)
        q_end_date = q_start_date + relativedelta(months=3) - timedelta(days=1)
        if q_end_date > today:
            q_end_date = today
        return (q_start_date, q_end_date)

    if period in ("ytd", "year_to_date"):
        return (today.replace(month=1, day=1), today)

    if period == "last_year":
        return (today.replace(year=today.year - 1, month=1, day=1), today.replace(year=today.year - 1, month=12, day=31))

    if period == "last_year_ytd":
        return (today.replace(year=today.year - 1, month=1, day=1), today.replace(year=today.year - 1, month=today.month, day=today.day))

    return (None, None)


def _compute_variance(current_total: float, previous_total: float) -> dict:
    amount = current_total - previous_total
    percent = ((current_total - previous_total) / previous_total * 100) if previous_total != 0 else 0.0
    return {
        "amount": round(amount, 2),
        "percent": round(percent, 2),
        "trend": "up" if amount > 0 else ("down" if amount < 0 else "flat"),
    }


def compare_trial_balance(db: Session, as_of_date: date | None, compare_date: date | None) -> dict:
    current = frs.get_trial_balance(db, as_of_date)
    previous = frs.get_trial_balance(db, compare_date)

    combined = []
    cur_map = {a["account_code"]: a for a in current["accounts"]}
    prev_map = {a["account_code"]: a for a in previous["accounts"]}
    all_codes = set(list(cur_map.keys()) + list(prev_map.keys()))

    for code in sorted(all_codes):
        cur = cur_map.get(code, {})
        prev = prev_map.get(code, {})
        cur_bal = cur.get("balance", 0)
        prev_bal = prev.get("balance", 0)
        combined.append({
            "account_code": code,
            "account_name": cur.get("account_name") or prev.get("account_name", ""),
            "account_type": cur.get("account_type") or prev.get("account_type", ""),
            "current_balance": cur_bal,
            "previous_balance": prev_bal,
            "variance": _compute_variance(cur_bal, prev_bal),
        })

    return {
        "as_of_date": as_of_date.isoformat() if as_of_date else current["as_of_date"],
        "compare_date": compare_date.isoformat() if compare_date else previous["as_of_date"],
        "accounts": combined,
        "current_total_debit": current.get("total_debit", 0),
        "current_total_credit": current.get("total_credit", 0),
        "previous_total_debit": previous.get("total_debit", 0),
        "previous_total_credit": previous.get("total_credit", 0),
    }


def compare_profit_loss(
    db: Session,
    from_date: date, to_date: date,
    compare_from: date, compare_to: date,
) -> dict:
    current = frs.get_profit_loss(db, from_date, to_date)
    previous = frs.get_profit_loss(db, compare_from, compare_to)

    return {
        "from_date": from_date.isoformat(),
        "to_date": to_date.isoformat(),
        "compare_from": compare_from.isoformat(),
        "compare_to": compare_to.isoformat(),
        "current": current,
        "previous": previous,
        "revenue_variance": _compute_variance(current.get("total_revenue", 0), previous.get("total_revenue", 0)),
        "expense_variance": _compute_variance(current.get("total_expense", 0), previous.get("total_expense", 0)),
        "net_income_variance": _compute_variance(current.get("net_income", 0), previous.get("net_income", 0)),
    }


def compare_balance_sheet(db: Session, as_of_date: date | None, compare_date: date | None) -> dict:
    current = frs.get_balance_sheet(db, as_of_date)
    previous = frs.get_balance_sheet(db, compare_date)

    return {
        "as_of_date": as_of_date.isoformat() if as_of_date else current["as_of_date"],
        "compare_date": compare_date.isoformat() if compare_date else previous["as_of_date"],
        "current": current,
        "previous": previous,
        "assets_variance": _compute_variance(current.get("total_assets", 0), previous.get("total_assets", 0)),
        "liabilities_variance": _compute_variance(current.get("total_liabilities", 0), previous.get("total_liabilities", 0)),
        "equity_variance": _compute_variance(current.get("total_equity", 0), previous.get("total_equity", 0)),
    }


def compare_cash_flow(
    db: Session,
    from_date: date, to_date: date,
    compare_from: date, compare_to: date,
) -> dict:
    current = frs.get_cash_flow(db, from_date, to_date)
    previous = frs.get_cash_flow(db, compare_from, compare_to)

    return {
        "from_date": from_date.isoformat(),
        "to_date": to_date.isoformat(),
        "compare_from": compare_from.isoformat(),
        "compare_to": compare_to.isoformat(),
        "current": current,
        "previous": previous,
        "operating_variance": _compute_variance(current.get("net_operating", 0), previous.get("net_operating", 0)),
        "net_change_variance": _compute_variance(current.get("net_change", 0), previous.get("net_change", 0)),
    }
