"""Parser stage: converts raw document bytes into text."""

from typing import ClassVar

from src.application.ingestion.context import IngestionContext


class Parser:
    """Parse raw document bytes into text."""

    SUPPORTED_MIME_TYPES: ClassVar[set[str]] = {
        "text/plain",
        "text/markdown",
        "text/csv",
        "text/html",
    }

    def execute(self, context: IngestionContext) -> IngestionContext:
        """Parse the document content."""

        mime_type = context.document_input.mime_type

        if mime_type not in self.SUPPORTED_MIME_TYPES:
            raise ValueError(
                f"Unsupported MIME type for parser: {mime_type}"
            )

        context.parsed_content = context.document_input.content.decode(
            "utf-8"
        )

        context.status = "parsed"

        return context