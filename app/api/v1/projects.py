"""Project management endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])
DatabaseSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(request: ProjectCreate, session: DatabaseSession, user: CurrentUser) -> Project:
    return project_service.create_project(session, user, request)


@router.get("", response_model=list[ProjectResponse])
def list_projects(session: DatabaseSession, user: CurrentUser) -> list[Project]:
    return project_service.list_projects(session, user)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: UUID, session: DatabaseSession, user: CurrentUser) -> Project:
    return project_service.get_project(session, project_id, user)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    request: ProjectUpdate,
    session: DatabaseSession,
    user: CurrentUser,
) -> Project:
    return project_service.update_project(session, project_id, user, request)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: UUID, session: DatabaseSession, user: CurrentUser) -> Response:
    project_service.delete_project(session, project_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
