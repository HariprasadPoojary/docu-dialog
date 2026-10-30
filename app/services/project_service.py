"""Project use cases and ownership enforcement."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User
from app.repositories import project_repository
from app.schemas.project import ProjectCreate, ProjectUpdate


def list_projects(session: Session, user: User) -> list[Project]:
    return project_repository.list_for_owner(session, user.id)


def get_project(session: Session, project_id: UUID, user: User) -> Project:
    project = project_repository.get_for_owner(session, project_id, user.id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def create_project(session: Session, user: User, request: ProjectCreate) -> Project:
    project = project_repository.create(
        session,
        owner_id=user.id,
        name=request.name,
        description=request.description,
    )
    try:
        session.commit()
        session.refresh(project)
    except Exception:
        session.rollback()
        raise
    return project


def update_project(
    session: Session,
    project_id: UUID,
    user: User,
    request: ProjectUpdate,
) -> Project:
    project = get_project(session, project_id, user)
    for field_name in request.model_fields_set:
        setattr(project, field_name, getattr(request, field_name))
    project_repository.save(session, project)
    try:
        session.commit()
        session.refresh(project)
    except Exception:
        session.rollback()
        raise
    return project


def delete_project(session: Session, project_id: UUID, user: User) -> None:
    project = get_project(session, project_id, user)
    project_repository.delete(session, project)
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
