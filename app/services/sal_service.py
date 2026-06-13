from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.models.ihe_models import Client, SalesInvoice, SalesInvoiceLine
from app.schemas.sal import ClientCreate, ClientUpdate, SalesInvoiceCreate


def get_clients(db: Session, skip: int = 0, limit: int = 100) -> list[Client]:
    stmt = select(Client).order_by(Client.ClientCode).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def get_client(db: Session, client_code: str) -> Client | None:
    return db.get(Client, client_code)


def create_client(db: Session, data: ClientCreate) -> Client:
    client = Client(**data.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def update_client(db: Session, client_code: str, data: ClientUpdate) -> Client | None:
    client = db.get(Client, client_code)
    if not client:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(client, key, val)
    db.commit()
    db.refresh(client)
    return client


def delete_client(db: Session, client_code: str) -> bool:
    client = db.get(Client, client_code)
    if not client:
        return False
    db.delete(client)
    db.commit()
    return True


def get_sales_invoices(
    db: Session,
    client_code: str | None = None,
    pnr_number: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[SalesInvoice], int]:
    stmt = select(SalesInvoice).options(joinedload(SalesInvoice.lines))
    count_stmt = select(func.count(SalesInvoice.InvoiceID))
    if client_code:
        stmt = stmt.where(SalesInvoice.ClientCode == client_code)
        count_stmt = count_stmt.where(SalesInvoice.ClientCode == client_code)
    if pnr_number:
        stmt = stmt.where(SalesInvoice.PNRNumber == pnr_number)
        count_stmt = count_stmt.where(SalesInvoice.PNRNumber == pnr_number)
    total = db.execute(count_stmt).scalar() or 0
    stmt = stmt.order_by(SalesInvoice.InvoiceDate.desc()).offset(skip).limit(limit)
    items = list(db.execute(stmt).scalars().unique().all())
    return items, total


def create_sales_invoice(db: Session, data: SalesInvoiceCreate) -> SalesInvoice:
    lines_data = data.lines
    inv_data = data.model_dump(exclude={"lines"})
    invoice = SalesInvoice(**inv_data)
    db.add(invoice)
    db.flush()
    for line_data in lines_data:
        line = SalesInvoiceLine(InvoiceID=invoice.InvoiceID, **line_data.model_dump())
        db.add(line)
    db.commit()
    db.refresh(invoice)
    return invoice


def get_sales_invoice(db: Session, invoice_id: int) -> SalesInvoice | None:
    stmt = select(SalesInvoice).where(SalesInvoice.InvoiceID == invoice_id).options(joinedload(SalesInvoice.lines))
    return db.execute(stmt).unique().scalar_one_or_none()


def update_sales_invoice(db: Session, invoice_id: int, data) -> SalesInvoice | None:
    invoice = db.get(SalesInvoice, invoice_id)
    if not invoice:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(invoice, key, val)
    db.commit()
    db.refresh(invoice)
    return invoice


def delete_sales_invoice(db: Session, invoice_id: int) -> bool:
    invoice = db.get(SalesInvoice, invoice_id)
    if not invoice:
        return False
    db.delete(invoice)
    db.commit()
    return True
