"""Cleaner stage: normalize parsed document text."""

import re

from src.application.ingestion.context import IngestionContext


class Cleaner:
    """Clean and normalize parsed document text."""

    def execute(self, context: IngestionContext) -> IngestionContext:
        """Clean parsed content."""

        if context.parsed_content is None:
            raise ValueError(
                "Cannot clean document without parsed content"
            )

        content = context.parsed_content

        # Normalize line endings.
        content = content.replace("\r\n", "\n")
        content = content.replace("\r", "\n")

        # Remove trailing whitespace from each line.
        content = "\n".join(
            line.rstrip()
            for line in content.splitlines()
        )

        # Collapse repeated spaces and tabs.
        content = re.sub(r"[ \t]+", " ", content)

        # Collapse excessive blank lines.
        content = re.sub(r"\n{3,}", "\n\n", content)

        # Remove leading/trailing whitespace.
        content = content.strip()

        context.cleaned_content = content
        context.status = "cleaned"

        return context