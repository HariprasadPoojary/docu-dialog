"""Basic process health endpoints."""

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_engine

router = APIRouter(tags=["health"])


@router.get("/healthz", summary="Liveness check")
def healthcheck() -> dict[str, str]:
    """Report that the API process is running."""

    return {"status": "ok"}


@router.get("/readyz", summary="Readiness check")
def readiness() -> dict[str, str]:
    """Check that the configured database can accept a simple query."""

    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except (RuntimeError, SQLAlchemyError) as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc

    return {"status": "ok", "database": "ok"}
