"""Parser selection by mime type."""

from src.infrastructure.parsers.base import Parser
from src.infrastructure.parsers.txt_parser import TxtParser


class ParserFactory:
    """Registry mapping mime types to parser instances."""

    def __init__(self) -> None:
        self._parsers: dict[str, Parser] = {}
        self.register("text/plain", TxtParser())

    def register(self, mime_type: str, parser: Parser) -> None:
        self._parsers[mime_type] = parser

    def get(self, mime_type: str) -> Parser:
        try:
            return self._parsers[mime_type]
        except KeyError:
            raise ValueError(f"No parser registered for mime type {mime_type!r}") from None