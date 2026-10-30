"""Basic process health endpoints."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthz", summary="Liveness check")
def healthcheck() -> dict[str, str]:
    """Report that the API process is running."""

    return {"status": "ok"}


@router.get("/readyz", summary="Readiness check")
def readiness() -> dict[str, str]:
    """Report that the app is ready; dependency checks are added with database wiring."""

    return {"status": "ok"}
