"""Document parsers."""

from src.infrastructure.parsers.base import Parser
from src.infrastructure.parsers.factory import ParserFactory
from src.infrastructure.parsers.txt_parser import TxtParser

__all__ = ["Parser", "ParserFactory", "TxtParser"]