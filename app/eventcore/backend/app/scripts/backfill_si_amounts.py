"""Backfill sales_invoice.total_amount from line items (unit_price * quantity)."""
import asyncio
import sys
from decimal import Decimal
from sqlalchemy import select, func
from app.database import SessionLocal
from app.models.sales_invoice import SalesInvoice, SalesInvoiceLineItem


async def backfill():
    async with SessionLocal() as db:
        result = await db.execute(select(SalesInvoice).order_by(SalesInvoice.invoice_number))
        invoices = result.scalars().all()
        updated = 0
        skipped = 0
        for inv in invoices:
            result = await db.execute(
                select(func.coalesce(func.sum(SalesInvoiceLineItem.total_amount), 0))
                .where(SalesInvoiceLineItem.invoice_id == inv.id)
            )
            line_total = result.scalar() or Decimal(0)
            if line_total > 0 and (inv.total_amount is None or inv.total_amount == 0):
                inv.total_amount = line_total
                inv.subtotal = line_total
                inv.vat_amount = round(line_total * Decimal("0.14"), 2)
                updated += 1
            else:
                skipped += 1
        await db.flush()
        await db.commit()
        print(f"Backfilled: {updated} invoices")
        print(f"Skipped (no line data or already has amount): {skipped}")
        print(f"Total invoices: {len(invoices)}")
        # Print non-zero results
        result = await db.execute(
            select(SalesInvoice).where(SalesInvoice.total_amount > 0)
            .order_by(SalesInvoice.invoice_number)
        )
        for inv in result.scalars().all():
            print(f"  {inv.invoice_number}: ${float(inv.total_amount):.2f}")


if __name__ == "__main__":
    asyncio.run(backfill())
