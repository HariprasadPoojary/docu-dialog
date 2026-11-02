"""Embedding adapter for the configured OpenAI model."""

from langchain_openai import OpenAIEmbeddings

from app.core.config import Settings
from app.ingestion.chunking import TextChunk
from app.models.chunk import EMBEDDING_DIMENSIONS


def embed_chunks(chunks: list[TextChunk], settings: Settings) -> list[list[float]]:
    """Embed text in bounded batches and ensure vectors match the pgvector schema."""

    if settings.openai_api_key is None:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    if not chunks:
        return []

    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key.get_secret_value(),
    )
    vectors: list[list[float]] = []
    batch_size = 64
    for offset in range(0, len(chunks), batch_size):
        batch = chunks[offset : offset + batch_size]
        vectors.extend(embeddings.embed_documents([chunk.content for chunk in batch]))

    if len(vectors) != len(chunks) or any(len(vector) != EMBEDDING_DIMENSIONS for vector in vectors):
        raise ValueError(f"Embedding model must return {EMBEDDING_DIMENSIONS}-dimension vectors")
    return vectors
