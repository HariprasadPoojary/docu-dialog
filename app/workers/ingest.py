"""Database-backed worker for queued document indexing jobs."""

import logging
import time
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import case, select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.ingestion.pipeline import index_document
from app.models.document import Document, DocumentStatus

logger = logging.getLogger("docudialog.ingestion")


def requeue_stale_documents(session: Session) -> int:
    """Recover jobs left processing after a worker stopped unexpectedly."""

    settings = get_settings()
    stale_before = datetime.now(UTC) - timedelta(seconds=settings.ingestion_stale_after_seconds)
    statement = (
        update(Document)
        .where(
            Document.status == DocumentStatus.PROCESSING.value,
            Document.updated_at < stale_before,
        )
        .values(
            status=case(
                (Document.ingestion_attempts < settings.max_ingestion_attempts, DocumentStatus.QUEUED.value),
                else_=DocumentStatus.FAILED.value,
            ),
            error_message="Worker stopped during processing; retry if needed.",
            updated_at=datetime.now(UTC),
        )
    )
    result = session.execute(statement)
    session.commit()
    return result.rowcount or 0


def claim_next_document(session: Session) -> tuple[UUID, int] | None:
    """Atomically claim one queued document using PostgreSQL skip-locked semantics."""

    statement = (
        select(Document)
        .where(Document.status == DocumentStatus.QUEUED.value)
        .order_by(Document.created_at, Document.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    document = session.scalar(statement)
    if document is None:
        return None

    document.status = DocumentStatus.PROCESSING.value
    document.ingestion_attempts += 1
    document.error_message = None
    attempt = document.ingestion_attempts
    document_id = document.id
    session.commit()
    return document_id, attempt


def _record_failure(session: Session, document_id: UUID, attempt: int, error: Exception) -> None:
    settings = get_settings()
    document = session.scalar(
        select(Document)
        .where(
            Document.id == document_id,
            Document.status == DocumentStatus.PROCESSING.value,
            Document.ingestion_attempts == attempt,
        )
        .with_for_update()
    )
    if document is None:
        return

    document.status = (
        DocumentStatus.QUEUED.value
        if attempt < settings.max_ingestion_attempts
        else DocumentStatus.FAILED.value
    )
    document.error_message = f"Indexing failed ({type(error).__name__}). See worker logs."
    session.commit()


def process_next_document() -> bool:
    """Claim and process one queued document; return whether work was found."""

    session_factory = get_session_factory()
    with session_factory() as session:
        claimed = claim_next_document(session)
    if claimed is None:
        return False

    document_id, attempt = claimed
    try:
        with session_factory() as session:
            index_document(session, document_id, attempt, get_settings())
    except Exception as exc:
        logger.error(
            "Document indexing failed",
            extra={"document_id": str(document_id), "attempt": attempt, "error_type": type(exc).__name__},
        )
        with session_factory() as session:
            _record_failure(session, document_id, attempt, exc)
    return True


def run_worker() -> None:
    """Poll PostgreSQL for queued documents until interrupted."""

    settings = get_settings()
    if settings.openai_api_key is None:
        raise RuntimeError("Set OPENAI_API_KEY before starting the ingestion worker")

    logger.info("Document ingestion worker started")
    session_factory = get_session_factory()
    while True:
        try:
            with session_factory() as session:
                recovered = requeue_stale_documents(session)
            if recovered:
                logger.warning("Recovered stale ingestion jobs", extra={"count": recovered})
            process_next_document()
        except Exception as exc:
            logger.error("Ingestion worker cycle failed", extra={"error_type": type(exc).__name__})
        time.sleep(settings.ingestion_poll_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    run_worker()
