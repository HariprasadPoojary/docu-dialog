"""Project document management endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services import document_service

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])
DatabaseSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("", response_model=list[DocumentResponse], status_code=status.HTTP_201_CREATED)
def upload_documents(
    project_id: UUID,
    session: DatabaseSession,
    user: CurrentUser,
    files: Annotated[list[UploadFile], File(description="One or more project documents")],
) -> list[DocumentResponse]:
    return document_service.upload_documents(session, project_id, user, files)


@router.get("", response_model=list[DocumentResponse])
def list_documents(project_id: UUID, session: DatabaseSession, user: CurrentUser) -> list[DocumentResponse]:
    return document_service.list_documents(session, project_id, user)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    project_id: UUID,
    document_id: UUID,
    session: DatabaseSession,
    user: CurrentUser,
) -> Response:
    document_service.delete_document(session, project_id, document_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
