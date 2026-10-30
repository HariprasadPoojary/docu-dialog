"""Database operations for projects, always scoped to their owner."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project


def list_for_owner(session: Session, owner_id: UUID) -> list[Project]:
    """Return only projects owned by the given user."""

    statement = select(Project).where(Project.owner_id == owner_id).order_by(Project.created_at.desc())
    return list(session.scalars(statement))


def get_for_owner(session: Session, project_id: UUID, owner_id: UUID) -> Project | None:
    """Find a project only when it belongs to the given user."""

    statement = select(Project).where(Project.id == project_id, Project.owner_id == owner_id)
    return session.scalar(statement)


def create(session: Session, *, owner_id: UUID, name: str, description: str | None) -> Project:
    """Insert a project for the given owner."""

    project = Project(owner_id=owner_id, name=name, description=description)
    session.add(project)
    session.flush()
    return project


def save(session: Session, project: Project) -> Project:
    """Persist project updates."""

    session.add(project)
    session.flush()
    return project


def delete(session: Session, project: Project) -> None:
    """Stage deletion of a project; the service commits the transaction."""

    session.delete(project)
