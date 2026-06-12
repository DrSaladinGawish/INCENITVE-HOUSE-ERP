from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.models.ihe_models import ChartOfAccounts, JournalVoucher, JournalVoucherLine


def get_trial_balance(
    db: Session,
    as_of_date: date | None = None,
) -> list[dict]:
    stmt = (
        select(
            ChartOfAccounts.AccountCode,
            ChartOfAccounts.AccountName,
            ChartOfAccounts.AccountType,
            func.coalesce(func.sum(JournalVoucherLine.DebitAmount), 0).label("total_debit"),
            func.coalesce(func.sum(JournalVoucherLine.CreditAmount), 0).label("total_credit"),
        )
        .select_from(ChartOfAccounts)
        .outerjoin(
            JournalVoucherLine,
            ChartOfAccounts.AccountCode == JournalVoucherLine.AccountCode,
        )
        .outerjoin(
            JournalVoucher,
            and_(
                JournalVoucher.JVNumber == JournalVoucherLine.JVNumber,
                JournalVoucher.JVDate <= as_of_date if as_of_date else True,
            ),
        )
        .group_by(ChartOfAccounts.AccountCode, ChartOfAccounts.AccountName, ChartOfAccounts.AccountType)
        .order_by(ChartOfAccounts.AccountCode)
    )
    rows = db.execute(stmt).fetchall()

    result = []
    total_dr = Decimal("0.00")
    total_cr = Decimal("0.00")
    for row in rows:
        dr = Decimal(str(row.total_debit or 0))
        cr = Decimal(str(row.total_credit or 0))
        balance = dr - cr
        total_dr += dr
        total_cr += cr
        result.append({
            "account_code": row.AccountCode,
            "account_name": row.AccountName,
            "account_type": row.AccountType,
            "debit": float(dr),
            "credit": float(cr),
            "balance": float(balance),
        })

    return {
        "as_of_date": as_of_date.isoformat() if as_of_date else datetime.now().strftime("%Y-%m-%d"),
        "accounts": result,
        "total_debit": float(total_dr),
        "total_credit": float(total_cr),
    }


def get_profit_loss(
    db: Session,
    from_date: date,
    to_date: date,
) -> dict:
    revenue_types = ["Revenue", "Income"]
    expense_types = ["Expense", "Cost of Goods Sold", "COGS"]

    revenue_stmt = (
        select(
            ChartOfAccounts.AccountCode,
            ChartOfAccounts.AccountName,
            func.coalesce(func.sum(JournalVoucherLine.CreditAmount), 0)
            - func.coalesce(func.sum(JournalVoucherLine.DebitAmount), 0).label("amount"),
        )
        .select_from(ChartOfAccounts)
        .outerjoin(
            JournalVoucherLine,
            ChartOfAccounts.AccountCode == JournalVoucherLine.AccountCode,
        )
        .outerjoin(
            JournalVoucher,
            and_(
                JournalVoucher.JVNumber == JournalVoucherLine.JVNumber,
                JournalVoucher.JVDate.between(from_date, to_date),
            ),
        )
        .where(ChartOfAccounts.AccountType.in_(revenue_types))
        .group_by(ChartOfAccounts.AccountCode, ChartOfAccounts.AccountName)
        .order_by(ChartOfAccounts.AccountCode)
    )
    revenues = db.execute(revenue_stmt).fetchall()

    expense_stmt = (
        select(
            ChartOfAccounts.AccountCode,
            ChartOfAccounts.AccountName,
            func.coalesce(func.sum(JournalVoucherLine.DebitAmount), 0)
            - func.coalesce(func.sum(JournalVoucherLine.CreditAmount), 0).label("amount"),
        )
        .select_from(ChartOfAccounts)
        .outerjoin(
            JournalVoucherLine,
            ChartOfAccounts.AccountCode == JournalVoucherLine.AccountCode,
        )
        .outerjoin(
            JournalVoucher,
            and_(
                JournalVoucher.JVNumber == JournalVoucherLine.JVNumber,
                JournalVoucher.JVDate.between(from_date, to_date),
            ),
        )
        .where(ChartOfAccounts.AccountType.in_(expense_types))
        .group_by(ChartOfAccounts.AccountCode, ChartOfAccounts.AccountName)
        .order_by(ChartOfAccounts.AccountCode)
    )
    expenses = db.execute(expense_stmt).fetchall()

    rev_items = []
    total_revenue = Decimal("0.00")
    for r in revenues:
        amt = Decimal(str(r.amount or 0))
        rev_items.append({"account_code": r.AccountCode, "account_name": r.AccountName, "amount": float(amt)})
        total_revenue += amt

    exp_items = []
    total_expense = Decimal("0.00")
    for e in expenses:
        amt = Decimal(str(e.amount or 0))
        exp_items.append({"account_code": e.AccountCode, "account_name": e.AccountName, "amount": float(amt)})
        total_expense += amt

    net_income = float(total_revenue - total_expense)

    return {
        "from_date": from_date.isoformat(),
        "to_date": to_date.isoformat(),
        "revenues": rev_items,
        "total_revenue": float(total_revenue),
        "expenses": exp_items,
        "total_expense": float(total_expense),
        "net_income": net_income,
    }


def get_balance_sheet(
    db: Session,
    as_of_date: date | None = None,
) -> dict:
    asset_types = ["Asset", "Current Asset", "Fixed Asset", "Non-Current Asset"]
    liability_types = ["Liability", "Current Liability", "Non-Current Liability"]
    equity_types = ["Equity", "Capital", "Retained Earnings"]

    stmt = (
        select(
            ChartOfAccounts.AccountType,
            ChartOfAccounts.AccountCode,
            ChartOfAccounts.AccountName,
            func.coalesce(func.sum(JournalVoucherLine.DebitAmount), 0).label("total_debit"),
            func.coalesce(func.sum(JournalVoucherLine.CreditAmount), 0).label("total_credit"),
        )
        .select_from(ChartOfAccounts)
        .outerjoin(
            JournalVoucherLine,
            ChartOfAccounts.AccountCode == JournalVoucherLine.AccountCode,
        )
        .outerjoin(
            JournalVoucher,
            and_(
                JournalVoucher.JVNumber == JournalVoucherLine.JVNumber,
                JournalVoucher.JVDate <= as_of_date if as_of_date else True,
            ),
        )
        .group_by(ChartOfAccounts.AccountType, ChartOfAccounts.AccountCode, ChartOfAccounts.AccountName)
        .order_by(ChartOfAccounts.AccountType, ChartOfAccounts.AccountCode)
    )
    rows = db.execute(stmt).fetchall()

    assets = []
    liabilities = []
    equity = []
    total_assets = Decimal("0.00")
    total_liabilities = Decimal("0.00")
    total_equity = Decimal("0.00")

    for row in rows:
        dr = Decimal(str(row.total_debit or 0))
        cr = Decimal(str(row.total_credit or 0))
        balance = dr - cr
        item = {"account_code": row.AccountCode, "account_name": row.AccountName, "balance": float(balance)}

        if row.AccountType in asset_types:
            assets.append(item)
            total_assets += balance if balance >= 0 else Decimal("0.00")
        elif row.AccountType in liability_types:
            liabilities.append(item)
            total_liabilities += abs(balance) if balance < 0 else balance
        elif row.AccountType in equity_types:
            equity.append(item)
            total_equity += balance

    return {
        "as_of_date": as_of_date.isoformat() if as_of_date else datetime.now().strftime("%Y-%m-%d"),
        "assets": assets,
        "total_assets": float(total_assets),
        "liabilities": liabilities,
        "total_liabilities": float(total_liabilities),
        "equity": equity,
        "total_equity": float(total_equity),
    }


def get_cash_flow(
    db: Session,
    from_date: date,
    to_date: date,
) -> dict:
    cash_stmt = select(ChartOfAccounts).where(
        ChartOfAccounts.AccountType.in_(["Current Asset", "Asset"]),
        ChartOfAccounts.AccountName.ilike("%cash%") | ChartOfAccounts.AccountName.ilike("%bank%"),
    )
    cash_accounts = db.execute(cash_stmt).scalars().all()
    cash_codes = [c.AccountCode for c in cash_accounts]

    if not cash_codes:
        cash_stmt = select(ChartOfAccounts).where(
            ChartOfAccounts.AccountType.in_(["Current Asset", "Asset"]),
        )
        cash_accounts = db.execute(cash_stmt).scalars().all()
        cash_codes = [c.AccountCode for c in cash_accounts]

    lines_stmt = (
        select(
            JournalVoucher.JVDate,
            JournalVoucher.Narration,
            JournalVoucherLine.AccountCode,
            JournalVoucherLine.DebitAmount,
            JournalVoucherLine.CreditAmount,
        )
        .select_from(JournalVoucherLine)
        .join(JournalVoucher, JournalVoucher.JVNumber == JournalVoucherLine.JVNumber)
        .where(
            JournalVoucherLine.AccountCode.in_(cash_codes),
            JournalVoucher.JVDate.between(from_date, to_date),
        )
        .order_by(JournalVoucher.JVDate)
    )
    rows = db.execute(lines_stmt).fetchall()

    operating = []
    investing = []
    financing = []
    net_operating = Decimal("0.00")
    net_investing = Decimal("0.00")
    net_financing = Decimal("0.00")

    for row in rows:
        dr = Decimal(str(row.DebitAmount or 0))
        cr = Decimal(str(row.CreditAmount or 0))
        net = cr - dr
        item = {"date": row.JVDate.isoformat() if row.JVDate else "", "narration": row.Narration or "", "amount": float(net)}

        operating.append(item)
        net_operating += net

    operating_balance = sum(Decimal(str(r.DebitAmount or 0)) - Decimal(str(r.CreditAmount or 0)) for r in rows)

    return {
        "from_date": from_date.isoformat(),
        "to_date": to_date.isoformat(),
        "cash_accounts": [{"code": c.AccountCode, "name": c.AccountName} for c in cash_accounts],
        "operating": operating,
        "net_operating": float(net_operating),
        "investing": investing,
        "net_investing": float(net_investing),
        "financing": financing,
        "net_financing": float(net_financing),
        "net_change": float(net_operating + net_investing + net_financing),
    }
