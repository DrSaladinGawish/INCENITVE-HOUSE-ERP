"""
P5 — HTMX Prescription Fragments for EventCore Job Pages

Renders prescription cards with Apply/Reject/In Progress actions
for display inside job detail views via HTMX.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.prescription import Prescription

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/prescriptions/htmx", tags=["prescriptions-htmx"])

PRIORITY_COLORS = {
    "high": "#ef4444",
    "medium": "#f59e0b",
    "low": "#22c55e",
}

STATUS_BORDER = {
    "applied": "#16a34a",
    "rejected": "#dc2626",
    "in_progress": "#2563eb",
    "pending": "#9ca3af",
}


def _card_html(p: Prescription) -> str:
    priority = getattr(p, "priority", "medium") or "medium"
    border_color = STATUS_BORDER.get(p.status, "#9ca3af")
    priority_color = PRIORITY_COLORS.get(priority, "#f59e0b")
    savings = getattr(p, "estimated_savings", None)
    notes = p.notes or ""
    medication = p.medication or ""
    doctor = p.prescribing_doctor or ""

    actions = ""
    if p.status == "pending":
        actions = f"""
        <div style="display:flex;gap:8px;margin-top:10px;">
            <button class="btn btn-sm btn-success"
                    hx-patch="/api/v1/prescriptions/htmx/{p.id}/status?status=applied"
                    hx-target="closest .prescription-card"
                    hx-swap="outerHTML"
                    style="padding:4px 12px;border:none;border-radius:4px;cursor:pointer;background:#16a34a;color:white;">
                Apply
            </button>
            <button class="btn btn-sm btn-danger"
                    hx-patch="/api/v1/prescriptions/htmx/{p.id}/status?status=rejected"
                    hx-target="closest .prescription-card"
                    hx-swap="outerHTML"
                    style="padding:4px 12px;border:none;border-radius:4px;cursor:pointer;background:#dc2626;color:white;">
                Reject
            </button>
            <button class="btn btn-sm btn-info"
                    hx-patch="/api/v1/prescriptions/htmx/{p.id}/status?status=in_progress"
                    hx-target="closest .prescription-card"
                    hx-swap="outerHTML"
                    style="padding:4px 12px;border:none;border-radius:4px;cursor:pointer;background:#2563eb;color:white;">
                In Progress
            </button>
        </div>
        """

    savings_html = ""
    if savings:
        savings_html = f'<div style="color:#16a34a;font-weight:600;margin-top:6px;">💰 Estimated Savings: ${float(savings):,.2f}</div>'

    return f"""
    <div class="prescription-card"
         style="border-left:4px solid {border_color};background:white;border-radius:8px;
                padding:14px 18px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.1);
                font-family:system-ui,-apple-system,sans-serif;font-size:14px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <span style="display:inline-block;width:10px;height:10px;border-radius:50%;
                             background:{priority_color};margin-right:6px;"></span>
                <strong>{medication}</strong>
                <span style="color:#6b7280;margin-left:8px;">— {doctor}</span>
            </div>
            <span style="font-size:12px;padding:2px 8px;border-radius:10px;
                         background:{border_color}20;color:{border_color};
                         font-weight:500;text-transform:uppercase;">
                {p.status}
            </span>
        </div>
        <div style="margin-top:6px;color:#4b5563;">
            {notes[:200]}{'...' if len(notes) > 200 else ''}
        </div>
        {savings_html}
        {actions}
    </div>
    """


def _badge_html(count: int) -> str:
    if count == 0:
        return '<span style="color:#9ca3af;font-size:12px;">No Rx</span>'
    color = "#ef4444" if count > 3 else "#f59e0b"
    return f'<span style="background:{color};color:white;padding:2px 8px;border-radius:10px;font-size:12px;font-weight:600;">{count} Rx</span>'


@router.get("/job/{job_id}", response_class=HTMLResponse)
async def prescriptions_for_job(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Prescription)
        .where(Prescription.external_id == job_id)
        .order_by(Prescription.created_at.desc())
    )
    records = result.scalars().all()

    if not records:
        return HTMLResponse('<div style="color:#9ca3af;padding:10px;">No prescriptions for this job.</div>')

    cards = "".join(_card_html(r) for r in records)
    return HTMLResponse(f'<div style="display:flex;flex-direction:column;gap:4px;">{cards}</div>')


@router.patch("/{prescription_id}/status", response_class=HTMLResponse)
async def update_prescription_status(
    prescription_id: UUID,
    status: str = Query(..., pattern="^(applied|rejected|in_progress)$"),
    db: AsyncSession = Depends(get_db),
):
    stmt = update(Prescription).where(Prescription.id == prescription_id).values(status=status)
    await db.execute(stmt)
    await db.flush()

    result = await db.execute(select(Prescription).where(Prescription.id == prescription_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Prescription not found")

    return HTMLResponse(_card_html(record))


@router.get("/badge/{job_id}", response_class=HTMLResponse)
async def prescription_badge(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Prescription).where(Prescription.external_id == job_id)
    )
    records = result.scalars().all()
    return HTMLResponse(_badge_html(len(records)))
