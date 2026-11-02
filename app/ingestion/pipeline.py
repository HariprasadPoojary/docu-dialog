"""Document processing pipeline from local bytes to persisted vector chunks."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.ingestion.chunking import split_sections
from app.ingestion.embeddings import embed_chunks
from app.ingestion.extractors import extract_sections
from app.models.chunk import DocumentChunk
from app.models.document import Document, DocumentStatus
from app.storage.local import LocalFileStorage


def index_document(
    session: Session,
    document_id: UUID,
    attempt: int,
    settings: Settings,
) -> bool:
    """Extract, chunk, embed, and commit one document if this worker still owns its lease."""

    document = session.get(Document, document_id)
    if document is None:
        return False

    storage_key = document.storage_key
    original_filename = document.original_filename
    session.commit()

    content = LocalFileStorage(settings.upload_directory).read(storage_key)
    chunks = split_sections(
        extract_sections(content, original_filename),
        original_filename,
        settings,
    )
    if not chunks:
        raise ValueError("No extractable text found")
    vectors = embed_chunks(chunks, settings)

    leased_document = session.scalar(
        select(Document)
        .where(
            Document.id == document_id,
            Document.status == DocumentStatus.PROCESSING.value,
            Document.ingestion_attempts == attempt,
        )
        .with_for_update()
    )
    if leased_document is None:
        return False

    session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
    session.add_all(
        DocumentChunk(
            document_id=document_id,
            project_id=leased_document.project_id,
            chunk_index=chunk_index,
            content=chunk.content,
            page_number=chunk.page_number,
            source_metadata=chunk.source_metadata,
            embedding=vector,
        )
        for chunk_index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))
    )
    leased_document.status = DocumentStatus.READY.value
    leased_document.error_message = None
    session.commit()
    return True
