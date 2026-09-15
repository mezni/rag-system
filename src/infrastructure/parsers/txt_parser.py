"""Plain-text parser."""

from src.infrastructure.parsers.base import Parser


class TxtParser(Parser):
    """Extracts text from plain-text content."""

    def parse(self, content: str) -> str:
        return content.replace("\r\n", "\n").replace("\r", "\n")