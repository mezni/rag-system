"""Chunker stage: split cleaned document text into chunks."""

from src.application.ingestion.context import IngestionContext
from src.domain.models import DocumentChunk


class Chunker:
    """Split cleaned document text into overlapping chunks."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")

        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size"
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def execute(self, context: IngestionContext) -> IngestionContext:
        """Split cleaned content into chunks."""

        if context.cleaned_content is None:
            raise ValueError(
                "Cannot chunk document without cleaned content"
            )

        text = context.cleaned_content

        if not text:
            context.chunks = []
            context.status = "chunked"
            return context

        document_id = context.document_input.source_id

        chunks: list[DocumentChunk] = []

        start = 0
        position = 0

        step = self.chunk_size - self.chunk_overlap

        while start < len(text) - self.chunk_overlap:
            end = min(
                start + self.chunk_size,
                len(text),
            )

            chunk_text = text[start:end]

            chunks.append(
                DocumentChunk(
                    chunk_id=f"{document_id}:{position}",
                    document_id=document_id,
                    text=chunk_text,
                    position=position,
                    metadata={
                        **context.document_input.metadata,
                        "source_type": context.document_input.source_type,
                        "document_name": context.document_input.name,
                    },
                )
            )

            position += 1
            start += step

        context.chunks = chunks
        context.status = "chunked"

        return context