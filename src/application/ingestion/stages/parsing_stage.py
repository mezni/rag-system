"""Parsing stage."""

from src.application.ingestion.context import IngestionContext
from src.application.ingestion.stage import Stage
from src.infrastructure.parsers.factory import ParserFactory


class ParsingStage(Stage):
    """Extracts plain text from the document via its mime type's parser."""

    def __init__(self, factory: ParserFactory) -> None:
        self._factory = factory

    def execute(self, context: IngestionContext) -> IngestionContext:
        document = context.document
        parser = self._factory.get(document.mime_type)
        context.parsed_content = parser.parse(document.content)
        return context