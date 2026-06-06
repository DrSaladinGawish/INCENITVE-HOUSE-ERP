from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ihe_models import (
    PNRMaster, SalesInvoice, PurchaseVoucher, BankTransaction, JournalVoucher, Client, Vendor
)
from app.pdf_generator import generate_list_pdf
from app.excel_generator import generate_excel, generate_csv

router = APIRouter(prefix="/api/export", tags=["Export"])

ENTITY_CONFIG = {
    "pnrs": {
        "model": PNRMaster,
        "title": "PNR List",
        "headers": ["PNR Number", "Client", "Event", "Start Date", "End Date", "Status"],
        "row_fn": lambda r: [r.PNRNumber, r.ClientCode or "", r.EventName or "", str(r.EventStartDate or ""), str(r.EventEndDate or ""), r.Status or ""],
    },
    "sales": {
        "model": SalesInvoice,
        "title": "Sales Invoices",
        "headers": ["Invoice #", "Client", "PNR", "Date", "Total", "Status"],
        "row_fn": lambda r: [r.InvoiceNumber or "", r.ClientCode or "", r.PNRNumber or "", str(r.InvoiceDate or ""), str(r.TotalValue or 0), r.PaymentStatus or ""],
    },
    "purchases": {
        "model": PurchaseVoucher,
        "title": "Purchase Vouchers",
        "headers": ["Voucher #", "PNR", "Date", "Total"],
        "row_fn": lambda r: [r.VoucherNumber or "", r.PNRNumber or "", str(r.InvoiceDate or ""), str(r.TotalValue or 0)],
    },
    "banking": {
        "model": BankTransaction,
        "title": "Bank Transactions",
        "headers": ["Date", "Payee", "Document #", "Withdrawal", "Deposit", "Balance"],
        "row_fn": lambda r: [str(r.TransactionDate or ""), r.Payee or "", r.DocumentNumber or "", str(r.Withdrawal or 0), str(r.Deposit or 0), str(r.RunningBalance or 0)],
    },
    "gl": {
        "model": JournalVoucher,
        "title": "Journal Vouchers",
        "headers": ["JV #", "Date", "Narration", "Total Debit", "Total Credit"],
        "row_fn": lambda r: [r.JVNumber or "", str(r.JVDate or ""), r.Narration or "", str(r.TotalDebit or 0), str(r.TotalCredit or 0)],
    },
}


@router.get("/{entity}")
def export_entity(entity: str, format: str = Query("pdf", regex="^(pdf|xlsx|csv)$"), db: Session = Depends(get_db)):
    config = ENTITY_CONFIG.get(entity)
    if not config:
        raise HTTPException(404, detail=f"Unknown entity: {entity}")
    model = config["model"]
    rows_data = db.execute(select(model).order_by(model.__table__.primary_key.columns.keys()[0])).scalars().all()
    rows = [config["row_fn"](r) for r in rows_data]

    if format == "pdf":
        buf = generate_list_pdf(config["title"], config["headers"], rows)
        return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={entity}.pdf"})
    elif format == "xlsx":
        sheets = [{"name": config["title"][:31], "headers": config["headers"], "rows": rows}]
        buf = generate_excel(sheets)
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename={entity}.xlsx"})
    else:
        csv = generate_csv(config["headers"], rows)
        return StreamingResponse(iter([csv]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={entity}.csv"})
