import pytest

from src.infrastructure.parsers.base import Parser
from src.infrastructure.parsers.factory import ParserFactory
from src.infrastructure.parsers.txt_parser import TxtParser


class _FakeParser(Parser):
    def __init__(self, result: str) -> None:
        self._result = result

    def parse(self, content: str) -> str:
        return self._result


def test_txt_parser_passthrough() -> None:
    assert TxtParser().parse("hello world") == "hello world"


def test_txt_parser_normalizes_line_endings() -> None:
    assert TxtParser().parse("a\r\nb\rc") == "a\nb\nc"


def test_factory_default_has_txt_parser() -> None:
    factory = ParserFactory()

    assert isinstance(factory.get("text/plain"), TxtParser)


def test_factory_get_unknown_mime_raises() -> None:
    factory = ParserFactory()

    with pytest.raises(ValueError, match="application/pdf"):
        factory.get("application/pdf")


def test_factory_register_overrides() -> None:
    factory = ParserFactory()
    fake = _FakeParser("parsed")
    factory.register("text/plain", fake)

    assert factory.get("text/plain") is fake


def test_factory_register_new_mime() -> None:
    factory = ParserFactory()
    fake = _FakeParser("parsed")
    factory.register("application/pdf", fake)

    assert factory.get("application/pdf") is fake