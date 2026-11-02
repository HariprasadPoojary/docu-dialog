"""Split extracted sections into overlapping, source-aware text chunks."""

from dataclasses import dataclass
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import Settings
from app.ingestion.extractors import ExtractedSection


@dataclass(frozen=True)
class TextChunk:
    """Chunk text and citation metadata before vectors are added."""

    content: str
    page_number: int | None
    source_metadata: dict[str, Any]


def split_sections(
    sections: list[ExtractedSection], filename: str, settings: Settings
) -> list[TextChunk]:
    """Split each PDF page or whole-document section without crossing source boundaries."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        add_start_index=True,
    )
    chunks: list[TextChunk] = []
    for section in sections:
        if not section.text.strip():
            continue
        source_metadata: dict[str, Any] = {"original_filename": filename}
        if section.section_name:
            source_metadata["section"] = section.section_name
        if section.page_number is not None:
            source_metadata["page_number"] = section.page_number

        for chunk in splitter.create_documents([section.text], metadatas=[source_metadata]):
            metadata = dict(chunk.metadata)
            start_index = metadata.pop("start_index", None)
            if start_index is not None:
                metadata["start_index"] = start_index
            chunks.append(
                TextChunk(
                    content=chunk.page_content,
                    page_number=section.page_number,
                    source_metadata=metadata,
                )
            )

    return chunks
