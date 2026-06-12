from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.audit_logger import AuditLogger

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("/activity")
async def get_activity(
    limit: int = Query(50, ge=1, le=200),
    target_type: str | None = Query(None),
    since_hours: int = Query(24, ge=1, le=720),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(hours=since_hours)
    logger = AuditLogger(db)
    logs = await logger.get_activity(
        limit=limit,
        target_type=target_type,
        since=since,
    )
    return {
        "count": len(logs),
        "since": since.isoformat(),
        "logs": [
            {
                "id": str(log.id),
                "action": log.action,
                "entity_type": log.target_type,
                "entity_id": log.target_id,
                "user_id": log.actor_id,
                "actor_name": log.actor_name,
                "created_at": log.timestamp.isoformat() if log.timestamp else None,
                "summary": f"{log.action} {log.target_type} {log.target_id or ''}",
                "description": log.description,
            }
            for log in logs
        ],
    }


@router.get("/activity/{entity_type}/{entity_id}")
async def get_entity_history(
    entity_type: str,
    entity_id: str,
    db: AsyncSession = Depends(get_db),
):
    logger = AuditLogger(db)
    logs = await logger.get_activity(target_type=entity_type, target_id=entity_id, limit=100)
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "total_changes": len(logs),
        "history": [
            {
                "id": str(log.id),
                "action": log.action,
                "user_id": log.actor_id,
                "actor_name": log.actor_name,
                "created_at": log.timestamp.isoformat() if log.timestamp else None,
                "description": log.description,
                "before": log.old_value,
                "after": log.new_value,
            }
            for log in logs
        ],
    }
