import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.models import EventDim


async def generate_event_id(db: AsyncSession) -> str:
    year = datetime.date.today().year
    result = await db.execute(
        select(func.count()).select_from(EventDim)
        .where(EventDim.event_code.like(f"EVT-{year}-%"))
    )
    count = result.scalar() or 0
    return f"EVT-{year}-{count + 1:03d}"


async def generate_pnr_id(db: AsyncSession) -> str:
    year = datetime.date.today().year
    result = await db.execute(
        select(func.count()).select_from(EventDim)
        .where(EventDim.event_code.like(f"PNR-{year}-%"))
    )
    count = result.scalar() or 0
    return f"PNR-{year}-{count + 1:03d}"
