"""Uploaded document persistence model."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.project import Project


class DocumentStatus(StrEnum):
    """Lifecycle states for a document and its future ingestion job."""

    QUEUED = "queued"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Document(Base):
    """Metadata for one uploaded file stored outside PostgreSQL."""

    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint("size_bytes >= 0", name="size_nonnegative"),
        CheckConstraint(
            "status IN ('queued', 'processing', 'ready', 'failed')", name="valid_status"
        ),
        Index("ix_documents_project_id", "project_id"),
        Index("ix_documents_project_status", "project_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    content_type: Mapped[str | None] = mapped_column(String(255))
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DocumentStatus.QUEUED.value,
        server_default=DocumentStatus.QUEUED.value,
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    project: Mapped[Project] = relationship(back_populates="documents")
