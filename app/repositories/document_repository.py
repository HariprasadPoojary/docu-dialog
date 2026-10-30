"""Database operations for project-scoped documents."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document


def list_for_project(session: Session, project_id: UUID) -> list[Document]:
    """Return documents belonging to one authorized project."""

    statement = (
        select(Document)
        .where(Document.project_id == project_id)
        .order_by(Document.created_at.desc(), Document.id)
    )
    return list(session.scalars(statement))


def get_for_project(session: Session, document_id: UUID, project_id: UUID) -> Document | None:
    """Find a document only when it belongs to the given project."""

    statement = select(Document).where(
        Document.id == document_id,
        Document.project_id == project_id,
    )
    return session.scalar(statement)
