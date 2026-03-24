from __future__ import annotations

from dataclasses import dataclass

from app.db.vector_store import FaissVectorStore
from app.services.embedding import EmbeddingService
from app.utils.pdf_loader import extract_text_from_pdf_bytes


@dataclass
class IngestionResult:
    filename: str
    chunks_created: int
    characters_processed: int


class IngestionService:
    """Handles upload-time PDF parsing, chunking, embedding, and persistence."""

    def __init__(
        self,
        vector_store: FaissVectorStore,
        embedding_service: EmbeddingService,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
    ) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size.")

        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def ingest_pdf(self, pdf_bytes: bytes, filename: str) -> IngestionResult:
        text = extract_text_from_pdf_bytes(pdf_bytes)
        if not text.strip():
            raise ValueError("No extractable text found in the PDF.")

        chunks = self._chunk_text(text)
        embeddings = self.embedding_service.embed_texts(chunks)
        inserted = self.vector_store.add_documents(
            texts=chunks,
            embeddings=embeddings,
            source=filename,
        )
        return IngestionResult(
            filename=filename,
            chunks_created=inserted,
            characters_processed=len(text),
        )

    def _chunk_text(self, text: str) -> list[str]:
        chunks: list[str] = []
        start = 0
        step = self.chunk_size - self.chunk_overlap
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start += step
        return chunks
