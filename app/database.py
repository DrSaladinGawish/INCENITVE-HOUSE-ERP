from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False,
)


def get_db():
    """Yields a DB session, or None if SQL Server is unavailable."""
    from app.db_safe import check_sql_available

    if not check_sql_available():
        yield None
        return
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db():
    """Create all tables if they don't exist."""
    from app.models import Base as ModelsBase
    ModelsBase.metadata.create_all(bind=sync_engine)
