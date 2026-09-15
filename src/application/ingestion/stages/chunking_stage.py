"""Chunking stage."""

from src.application.ingestion.context import IngestionContext
from src.application.ingestion.stage import Stage
from src.domain.models import Chunk


def chunk_text(text: str, chunk_size: int, overlap: int = 0) -> list[str]:
    """Split ``text`` into fixed-size pieces with an optional character overlap."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be in [0, chunk_size)")

    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        pieces.append(text[start:end])
        if end == len(text):
            break
        start += chunk_size - overlap
    return pieces


class ChunkingStage(Stage):
    """Splits cleaned content into fixed-size ``Chunk`` documents."""

    def __init__(self, chunk_size: int = 500, overlap: int = 0) -> None:
        self._chunk_size = chunk_size
        self._overlap = overlap

    def execute(self, context: IngestionContext) -> IngestionContext:
        if context.cleaned_content is None:
            raise ValueError("ChunkingStage requires cleaned content")

        document_id = context.document.source_id
        context.chunks = [
            Chunk(
                chunk_id=f"{document_id}#{index}",
                document_id=document_id,
                text=text,
                chunk_index=index,
            )
            for index, text in enumerate(
                chunk_text(context.cleaned_content, self._chunk_size, self._overlap)
            )
        ]
        return context