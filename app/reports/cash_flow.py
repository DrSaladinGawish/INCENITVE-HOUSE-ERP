from collections import defaultdict
from decimal import Decimal
from datetime import date
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.models.ihe_models import ChartOfAccounts, JournalVoucher, JournalVoucherLine


OPERATING_TYPES = {"REVENUE", "INCOME", "EXPENSE", "COST OF GOODS SOLD", "COGS", "COST OF SALES"}
INVESTING_TYPES = {"FIXED ASSET", "NON-CURRENT ASSET", "INTANGIBLE ASSET", "FIXED ASSETS"}
FINANCING_TYPES = {"LOAN", "EQUITY", "CAPITAL", "DIVIDEND", "LONG-TERM LIABILITY", "RETAINED EARNINGS"}


class CashFlowReport:
    def __init__(self, db: Session):
        self.db = db

    def generate(self, from_date: date, to_date: date) -> dict:
        cash_accounts = self._get_cash_accounts()
        if not cash_accounts:
            return self._empty_result(from_date, to_date)

        cash_codes = [c.AccountCode for c in cash_accounts]
        cash_type_map = {c.AccountCode: c.AccountName for c in cash_accounts}

        opening_balance = self._get_balance(cash_codes, from_date, exclude_date=True)
        closing_balance = self._get_balance(cash_codes, to_date)

        cash_lines = self._get_cash_lines(cash_codes, from_date, to_date)
        jv_groups = self._group_by_jv(cash_lines)

        operating, investing, financing = self._categorize(jv_groups, cash_codes)

        net_operating = sum(item["amount"] for item in operating)
        net_investing = sum(item["amount"] for item in investing)
        net_financing = sum(item["amount"] for item in financing)
        net_change = net_operating + net_investing + net_financing

        return {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "cash_accounts": [{"code": c, "name": cash_type_map[c]} for c in cash_codes],
            "opening_balance": round(float(opening_balance), 2),
            "closing_balance": round(float(closing_balance), 2),
            "operating": operating,
            "net_operating": round(net_operating, 2),
            "investing": investing,
            "net_investing": round(net_investing, 2),
            "financing": financing,
            "net_financing": round(net_financing, 2),
            "net_change": round(net_change, 2),
        }

    def _empty_result(self, from_date: date, to_date: date) -> dict:
        return {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "cash_accounts": [],
            "opening_balance": 0.0,
            "closing_balance": 0.0,
            "operating": [],
            "net_operating": 0.0,
            "investing": [],
            "net_investing": 0.0,
            "financing": [],
            "net_financing": 0.0,
            "net_change": 0.0,
        }

    def _get_cash_accounts(self) -> list:
        stmt = select(ChartOfAccounts).where(
            ChartOfAccounts.AccountType.in_(["Current Asset", "Asset"]),
            or_(
                ChartOfAccounts.AccountName.ilike("%cash%"),
                ChartOfAccounts.AccountName.ilike("%bank%"),
            ),
        )
        cash = self.db.execute(stmt).scalars().all()
        if not cash:
            stmt = select(ChartOfAccounts).where(
                ChartOfAccounts.AccountType.in_(["Current Asset", "Asset"]),
            )
            cash = self.db.execute(stmt).scalars().all()
        return cash

    def _get_balance(self, cash_codes: list[str], as_of: date, exclude_date: bool = False) -> Decimal:
        stmt = (
            select(
                func.coalesce(func.sum(JournalVoucherLine.DebitAmount), 0)
                - func.coalesce(func.sum(JournalVoucherLine.CreditAmount), 0)
            )
            .select_from(JournalVoucherLine)
            .join(JournalVoucher, JournalVoucher.JVNumber == JournalVoucherLine.JVNumber)
            .where(JournalVoucherLine.AccountCode.in_(cash_codes))
        )
        if exclude_date:
            stmt = stmt.where(JournalVoucher.JVDate < as_of)
        else:
            stmt = stmt.where(JournalVoucher.JVDate <= as_of)
        result = self.db.execute(stmt).scalar()
        return Decimal(str(result or 0))

    def _get_cash_lines(self, cash_codes: list[str], from_date: date, to_date: date) -> list:
        stmt = (
            select(
                JournalVoucher.JVNumber,
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
        return self.db.execute(stmt).fetchall()

    def _group_by_jv(self, cash_lines: list) -> dict:
        groups = defaultdict(list)
        for row in cash_lines:
            groups[row.JVNumber].append(row)
        return dict(groups)

    def _categorize(self, jv_groups: dict, cash_codes: list[str]) -> tuple[list, list, list]:
        operating = []
        investing = []
        financing = []

        for jv_number, lines in jv_groups.items():
            if not lines:
                continue
            jv_date = lines[0].JVDate
            narration = lines[0].Narration or ""

            contra_codes = set()
            net_flow = Decimal("0.00")
            for line in lines:
                if line.AccountCode in cash_codes:
                    net_flow += Decimal(str(line.DebitAmount or 0)) - Decimal(str(line.CreditAmount or 0))
                else:
                    contra_codes.add(line.AccountCode)

            if net_flow == 0:
                continue

            category = self._determine_category(list(contra_codes))

            item = {
                "date": jv_date.isoformat() if jv_date else "",
                "narration": narration,
                "amount": round(float(net_flow), 2),
                "jv_number": jv_number,
                "contra_accounts": list(contra_codes),
            }

            if category == "investing":
                investing.append(item)
            elif category == "financing":
                financing.append(item)
            else:
                operating.append(item)

        return operating, investing, financing

    def _determine_category(self, contra_codes: list[str]) -> str:
        if not contra_codes:
            return "operating"

        stmt = select(ChartOfAccounts.AccountCode, ChartOfAccounts.AccountType).where(
            ChartOfAccounts.AccountCode.in_(contra_codes)
        )
        rows = self.db.execute(stmt).fetchall()

        for row in rows:
            atype = (row.AccountType or "").upper().strip()
            if any(t in atype for t in FINANCING_TYPES):
                return "financing"
        for row in rows:
            atype = (row.AccountType or "").upper().strip()
            if any(t in atype for t in INVESTING_TYPES):
                return "investing"
        for row in rows:
            atype = (row.AccountType or "").upper().strip()
            if any(t in atype for t in OPERATING_TYPES):
                return "operating"
        for row in rows:
            atype = (row.AccountType or "").upper().strip()
            if "LIABILITY" in atype:
                return "financing"
        for row in rows:
            atype = (row.AccountType or "").upper().strip()
            if "ASSET" in atype and "CURRENT" not in atype:
                return "investing"

        return "operating"
