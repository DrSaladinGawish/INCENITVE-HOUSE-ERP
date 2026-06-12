import json
from datetime import datetime, timezone
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AuditLogger:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log(
        self,
        action: str,
        target_type: str,
        target_id: str | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
        description: str | None = None,
        actor_id: str | None = None,
        actor_name: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ):
        entry = AuditLog(
            timestamp=_utcnow(),
            actor_id=actor_id,
            actor_name=actor_name,
            action=action,
            target_type=target_type,
            target_id=target_id,
            old_value=json.dumps(old_value, default=str) if old_value else None,
            new_value=json.dumps(new_value, default=str) if new_value else None,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.session.add(entry)
        return entry

    async def get_activity(
        self,
        limit: int = 50,
        target_type: str | None = None,
        target_id: str | None = None,
        since: datetime | None = None,
    ):
        q = select(AuditLog).order_by(desc(AuditLog.id))
        if target_type:
            q = q.where(AuditLog.target_type == target_type)
        if target_id:
            q = q.where(AuditLog.target_id == target_id)
        if since:
            q = q.where(AuditLog.timestamp >= since)
        q = q.limit(limit)
        result = await self.session.execute(q)
        return result.scalars().all()
