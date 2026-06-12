"""
EventCore /or-insights Receiver Endpoint
Receives OR analysis from BIO-ERP (Doctor, port 8000) and persists to DB.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.models.or_insight import ORInsight

router = APIRouter(prefix="/api/v1/jobs", tags=["OR Insights"])

class ORInsightPayload(BaseModel):
    job_id: str
    module: str
    integration_type: str = "reverse_flow_p2"
    timestamp: datetime
    data: Dict[str, Any]
    ui_render_hints: Optional[Dict[str, Any]] = None

class ORInsightResponse(BaseModel):
    success: bool
    job_id: str
    insight_id: str
    message: str

@router.post("/{job_id}/or-insights", response_model=ORInsightResponse)
async def receive_or_insights(job_id: str, payload: ORInsightPayload, db: AsyncSession = Depends(get_db)):
    """
    Receive OR analysis results from BIO-ERP (Doctor system)
    Called by P2 Reverse Flow when OR analysis completes
    """
    insight_id = f"OR-INS-{job_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    record = ORInsight(
        job_id=job_id,
        insight_id=insight_id,
        module=payload.module,
        integration_type=payload.integration_type,
        or_score=payload.data.get("or_score"),
        sensitivity_range=payload.data.get("sensitivity_range"),
        status=payload.data.get("status"),
        analysis_url=payload.data.get("analysis_url"),
        recommendations=payload.data.get("recommendations"),
        raw_data=payload.data,
        ui_render_hints=payload.ui_render_hints or {},
        received_at=datetime.utcnow(),
    )
    db.add(record)
    await db.flush()

    return ORInsightResponse(
        success=True,
        job_id=job_id,
        insight_id=insight_id,
        message=f"OR insight received for job {job_id}"
    )

@router.get("/{job_id}/or-insights")
async def get_or_insights(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get all OR insights for a job (for job page display)"""
    result = await db.execute(
        select(ORInsight)
        .where(ORInsight.job_id == job_id)
        .order_by(ORInsight.created_at)
    )
    insights = result.scalars().all()

    if not insights:
        return {
            "job_id": job_id,
            "insights": [],
            "latest_score": None,
            "recommendations": [],
            "has_data": False
        }

    latest = insights[-1]

    return {
        "job_id": job_id,
        "insights_count": len(insights),
        "latest": {
            "insight_id": latest.insight_id,
            "timestamp": latest.received_at,
            "or_score": latest.or_score,
            "sensitivity_range": latest.sensitivity_range,
            "status": latest.status,
            "analysis_url": latest.analysis_url,
        },
        "all_recommendations": [
            rec for ins in insights
            for rec in (ins.recommendations or [])
        ],
        "ui_hints": latest.ui_render_hints or {},
        "has_data": True
    }

@router.get("/{job_id}/or-insights/badge")
async def get_or_insights_badge(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get compact badge data for job listing page"""
    result = await db.execute(
        select(ORInsight)
        .where(ORInsight.job_id == job_id)
        .order_by(ORInsight.created_at)
    )
    insights = result.scalars().all()

    if not insights:
        return {
            "job_id": job_id,
            "visible": False,
            "badge_text": None,
            "badge_color": None
        }

    latest = insights[-1]
    hints = latest.ui_render_hints or {}
    score = latest.or_score or 0

    return {
        "job_id": job_id,
        "visible": True,
        "badge_text": hints.get("badge_text", "OR Ready"),
        "badge_color": hints.get("badge_color", "#17a2b8"),
        "or_score": score,
        "modal_trigger": hints.get("modal_trigger", False),
        "display_section": hints.get("display_section", "cost_analysis_tab")
    }

@router.delete("/{job_id}/or-insights")
async def clear_or_insights(job_id: str, db: AsyncSession = Depends(get_db)):
    """Clear OR insights for a job (admin only)"""
    await db.execute(
        delete(ORInsight).where(ORInsight.job_id == job_id)
    )
    return {"success": True, "job_id": job_id, "message": "Insights cleared"}
