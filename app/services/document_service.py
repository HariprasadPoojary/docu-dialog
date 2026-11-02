"""Project-scoped upload, listing, and deletion use cases."""

import logging
import mimetypes
from pathlib import PurePosixPath
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Document, DocumentStatus
from app.models.user import User
from app.repositories import document_repository
from app.schemas.document import DocumentResponse
from app.services import project_service
from app.storage.local import LocalFileStorage, UploadTooLargeError

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".csv"}


def _safe_display_name(filename: str | None) -> str:
    """Keep only a display name and remove control characters and path segments."""

    normalized = (filename or "").replace("\\", "/")
    display_name = PurePosixPath(normalized).name
    display_name = "".join(
        character for character in display_name if ord(character) >= 32 and ord(character) != 127
    )
    display_name = display_name.strip()
    if not display_name or display_name in {".", ".."}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Each file must have a valid filename"
        )
    if len(display_name) > 512:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Filename exceeds 512 characters"
        )
    return display_name


def _validate_extension(filename: str) -> str:
    suffix = PurePosixPath(filename).suffix.casefold()
    if suffix not in ALLOWED_EXTENSIONS:
        supported = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Supported extensions: {supported}",
        )
    return suffix


def list_documents(session: Session, project_id: UUID, user: User) -> list[Document]:
    project_service.get_project(session, project_id, user)
    return document_repository.list_for_project(session, project_id)


def upload_documents(
    session: Session,
    project_id: UUID,
    user: User,
    uploads: list[UploadFile],
) -> list[Document]:
    project = project_service.get_project(session, project_id, user)
    settings = get_settings()
    if not uploads:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Select at least one file"
        )
    if len(uploads) > settings.max_upload_files:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Upload up to {settings.max_upload_files} files at a time",
        )

    validated: list[tuple[UploadFile, str, str]] = []
    for upload in uploads:
        display_name = _safe_display_name(upload.filename)
        suffix = _validate_extension(display_name)
        validated.append((upload, display_name, suffix))

    storage = LocalFileStorage(settings.upload_directory)
    stored_keys: list[str] = []
    documents: list[Document] = []
    request_bytes = 0

    try:
        for upload, display_name, suffix in validated:
            remaining_request_bytes = settings.max_upload_total_bytes - request_bytes
            if remaining_request_bytes <= 0:
                raise UploadTooLargeError
            max_bytes = min(settings.max_upload_bytes, remaining_request_bytes)
            try:
                storage_key, size_bytes = storage.save(upload.file, suffix, max_bytes)
            except UploadTooLargeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Upload exceeds the configured per-file or per-request size limit",
                ) from exc

            if size_bytes == 0:
                storage.delete(storage_key)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Empty files are not allowed"
                )

            stored_keys.append(storage_key)
            request_bytes += size_bytes
            documents.append(
                Document(
                    project_id=project.id,
                    original_filename=display_name,
                    storage_key=storage_key,
                    content_type=(
                        upload.content_type
                        or mimetypes.guess_type(display_name)[0]
                        or "application/octet-stream"
                    )[:255],
                    size_bytes=size_bytes,
                    status=DocumentStatus.QUEUED.value,
                )
            )

        session.add_all(documents)
        session.commit()
        return documents
    except Exception:
        session.rollback()
        for storage_key in stored_keys:
            try:
                storage.delete(storage_key)
            except OSError:
                logger.exception(
                    "Failed to clean up upload %s after a failed upload request", storage_key
                )
        raise


def delete_document(session: Session, project_id: UUID, document_id: UUID, user: User) -> None:
    project = project_service.get_project(session, project_id, user)
    document = document_repository.get_for_project(session, document_id, project.id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    storage_key = document.storage_key
    storage = LocalFileStorage(get_settings().upload_directory)
    session.delete(document)
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise

    try:
        storage.delete(storage_key)
    except OSError:
        logger.exception("Failed to remove stored file for document %s", document_id)


def retry_document(session: Session, project_id: UUID, document_id: UUID, user: User) -> Document:
    project = project_service.get_project(session, project_id, user)
    document = document_repository.get_for_project(session, document_id, project.id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if document.status != DocumentStatus.FAILED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only failed documents can be retried",
        )

    document.status = DocumentStatus.QUEUED.value
    document.ingestion_attempts = 0
    document.error_message = None
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    return document
