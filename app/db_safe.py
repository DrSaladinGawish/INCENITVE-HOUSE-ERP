"""
db_safe.py — Safe database dependency with graceful SQL Server fallback.
Returns mock data when SQL Server is offline instead of crashing with 500.
"""

import logging
from contextlib import contextmanager
from typing import Any, Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings

log = logging.getLogger(settings.APP_NAME)

_sql_available: Optional[bool] = None

MOCK_DASHBOARD = {
    "total_pnrs": 412,
    "active_pnrs": 38,
    "total_sales": 48200000.0,
    "total_purchases": 31700000.0,
    "bank_balance": 2100000.0,
    "outstanding_receivables": 8500000.0,
    "total_clients": 52,
    "total_vendors": 31,
}

MOCK_CLIENTS = [
    {"ClientCode": "CISCO", "ClientName": "CISCO Systems", "TaxID": "123456", "IsActive": True},
    {"ClientCode": "MSFT", "ClientName": "Microsoft Corp", "TaxID": "789012", "IsActive": True},
    {"ClientCode": "NOVQ", "ClientName": "Noventiq", "TaxID": "345678", "IsActive": True},
    {"ClientCode": "ABBT", "ClientName": "Abbott", "TaxID": "901234", "IsActive": True},
]

MOCK_PNRS = [
    {"PNRNumber": "V0563", "EventName": "CISCO Partner Summit", "Year": 2026, "Status": "Active"},
    {"PNRNumber": "V0564", "EventName": "Microsoft Ignite Roadshow", "Year": 2026, "Status": "Active"},
    {"PNRNumber": "V0565", "EventName": "Noventiq Partner Day", "Year": 2026, "Status": "Pending"},
]

MOCK_BANKS = [
    {"BankCode": "BNK_CUR", "BankName": "CIB EGP Account", "IsActive": True},
    {"BankCode": "BNK_SAV", "BankName": "HSBC USD Account", "IsActive": True},
    {"BankCode": "BNK_USD", "BankName": "QNB EGP Account", "IsActive": True},
    {"BankCode": "BNK_EUR", "BankName": "AAIB EGP Account", "IsActive": True},
]

MOCK_VENDORS = [
    {"VendorCode": "V001", "VendorName": "Grand Venue", "IsActive": True},
    {"VendorCode": "V002", "VendorName": "Catering Pro", "IsActive": True},
    {"VendorCode": "V003", "VendorName": "Transit Solutions", "IsActive": True},
]

MOCK_BUDGET_LINES = []

MOCK_ACCOUNTS = [
    {"AccountCode": "1001", "AccountName": "Cash on Hand", "AccountType": "Asset"},
    {"AccountCode": "2001", "AccountName": "Accounts Payable", "AccountType": "Liability"},
    {"AccountCode": "3001", "AccountName": "Revenue", "AccountType": "Revenue"},
    {"AccountCode": "4001", "AccountName": "Operating Expense", "AccountType": "Expense"},
]

MOCK_EMPLOYEES = [
    {"EmployeeCode": "E001", "EmployeeName": "Ahmed Hassan", "EmployeeType": "Manager", "IsActive": True},
    {"EmployeeCode": "E002", "EmployeeName": "Sara Ali", "EmployeeType": "Coordinator", "IsActive": True},
]

MOCK_VOUCHERS = []

MOCK_INVOICES = []

MOCK_TRANSACTIONS = []


def check_sql_available() -> bool:
    global _sql_available
    if _sql_available is not None:
        return _sql_available
    try:
        engine = create_engine(
            settings.SYNC_DATABASE_URL,
            echo=False,
            pool_size=1,
            max_overflow=0,
            pool_pre_ping=True,
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        _sql_available = True
        log.info("SQL Server connected")
    except Exception as e:
        _sql_available = False
        log.warning("SQL Server offline — fallback mode: %s", e)
    return _sql_available


def reset_connection_check():
    global _sql_available
    _sql_available = None


@contextmanager
def safe_db_session() -> Generator[Optional[Session], None, None]:
    if check_sql_available():
        try:
            engine = create_engine(
                settings.SYNC_DATABASE_URL,
                echo=False,
                pool_size=2,
                max_overflow=4,
                pool_pre_ping=True,
            )
            from sqlalchemy.orm import sessionmaker
            SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
            db = SessionLocal()
            try:
                yield db
            finally:
                db.close()
        except SQLAlchemyError as e:
            log.error("Session creation failed: %s", e)
            yield None
    else:
        yield None


def get_mock_data(table: str) -> list | dict:
    mapping = {
        "clients": MOCK_CLIENTS,
        "pnrs": MOCK_PNRS,
        "banks": MOCK_BANKS,
        "vendors": MOCK_VENDORS,
        "accounts": MOCK_ACCOUNTS,
        "employees": MOCK_EMPLOYEES,
        "budget_lines": MOCK_BUDGET_LINES,
        "invoices": MOCK_INVOICES,
        "vouchers": MOCK_VOUCHERS,
        "transactions": MOCK_TRANSACTIONS,
        "dashboard": MOCK_DASHBOARD,
    }
    return mapping.get(table, [])
