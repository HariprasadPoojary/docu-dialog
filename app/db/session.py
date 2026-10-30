"""SQLAlchemy engine, session factory, and FastAPI dependency."""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    """Create a process-wide engine when a database URL is configured."""

    database_url = get_settings().database_url
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    return create_engine(database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Return the shared SQLAlchemy session factory."""

    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        expire_on_commit=False,
    )


def get_db() -> Generator:
    """Yield a request-scoped database session and always close it."""

    with get_session_factory()() as session:
        yield session
