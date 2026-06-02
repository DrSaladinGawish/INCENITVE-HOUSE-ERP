"""PNR allocation and classification service."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.models.models import PNRDim, SalesInvoice, PurchaseInvoice, BankTransaction, PNRAllocationSummary


async def classify_pnr(pnr_id: int, pnr_type: str, db: AsyncSession) -> dict:
    result = await db.execute(select(PNRDim).where(PNRDim.pnr_id == pnr_id))
    pnr = result.scalar_one_or_none()
    if not pnr:
        raise ValueError("PNR not found")
    pnr.pnr_type = pnr_type
    await db.commit()
    return {"pnr_id": pnr_id, "pnr_code": pnr.pnr_code, "pnr_type": pnr_type}


async def get_allocation_report(db: AsyncSession, pnr_id: int = None) -> list:
    q = select(PNRDim)
    if pnr_id:
        q = q.where(PNRDim.pnr_id == pnr_id)
    result = await db.execute(q)
    pnrs = result.scalars().all()
    report = []
    for p in pnrs:
        s = await db.execute(select(func.count(SalesInvoice.inv_id), func.coalesce(func.sum(SalesInvoice.total_amount), 0)).where(SalesInvoice.pnr_id == p.pnr_id))
        s_cnt, s_amt = s.one()
        p = await db.execute(select(func.count(PurchaseInvoice.inv_id), func.coalesce(func.sum(PurchaseInvoice.total_amount), 0)).where(PurchaseInvoice.pnr_id == p.pnr_id))
        p_cnt, p_amt = p.one()
        b = await db.execute(select(func.count(BankTransaction.trnx_id), func.coalesce(func.sum(BankTransaction.egp_amount), 0)).where(BankTransaction.pnr_id == p.pnr_id))
        b_cnt, b_amt = b.one()
        report.append({
            "pnr_id": p.pnr_id, "pnr_code": p.pnr_code, "pnr_type": p.pnr_type,
            "sales_count": s_cnt, "sales_amount": float(s_amt),
            "purchase_count": p_cnt, "purchase_amount": float(p_amt),
            "bank_count": b_cnt, "bank_amount": float(b_amt),
        })
    return report


async def fuzzy_search(db: AsyncSession, query: str) -> list:
    pattern = f"%{query}%"
    result = await db.execute(
        select(PNRDim).where(or_(PNRDim.pnr_code.ilike(pattern), PNRDim.name.ilike(pattern)))
    )
    return result.scalars().all()
