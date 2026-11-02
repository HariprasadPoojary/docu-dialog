"""Text extraction for the supported document types."""

import csv
from dataclasses import dataclass
from io import BytesIO, StringIO
from pathlib import PurePosixPath

from docx import Document as WordDocument
from pypdf import PdfReader


@dataclass(frozen=True)
class ExtractedSection:
    """Extracted text with the source location needed for citations."""

    text: str
    page_number: int | None = None
    section_name: str | None = None


def extract_sections(content: bytes, filename: str) -> list[ExtractedSection]:
    """Extract text from an uploaded document without trusting its display path."""

    extension = PurePosixPath(filename).suffix.casefold()
    if extension == ".pdf":
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted:
            raise ValueError("Encrypted PDF files are not supported")
        return [
            ExtractedSection(text=page.extract_text() or "", page_number=page_number)
            for page_number, page in enumerate(reader.pages, start=1)
        ]

    if extension == ".docx":
        document = WordDocument(BytesIO(content))
        parts = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
        for table in document.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells)
                if row_text.strip(" |"):
                    parts.append(row_text)
        return [ExtractedSection(text="\n".join(parts))]

    text = content.decode("utf-8-sig")
    if extension == ".csv":
        rows = csv.reader(StringIO(text))
        text = "\n".join(" | ".join(cell.strip() for cell in row) for row in rows)
    elif extension not in {".txt", ".md"}:
        raise ValueError("Unsupported file type")

    return [ExtractedSection(text=text)]
