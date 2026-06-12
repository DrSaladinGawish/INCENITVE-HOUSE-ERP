async def generate_job_code(db_session, year: int, client_id) -> str:
    from sqlalchemy import select, func
    from app.models.job import Job

    from app.models.client import Client
    result = await db_session.execute(
        select(Client.client_code).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise ValueError(f"Client {client_id} not found")

    result = await db_session.execute(
        select(func.coalesce(func.max(Job.sequence), 200) + 1)
        .where(Job.year == year)
        .where(Job.client_id == client_id)
    )
    sequence = result.scalar()

    return f"{year:02d}.{client}.{sequence:03d}"
