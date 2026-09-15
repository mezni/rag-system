"""Cleaning stage."""

import re

from src.application.ingestion.context import IngestionContext
from src.application.ingestion.stage import Stage

_CRLF_RE = re.compile(r"\r\n|\r")
_HORIZONTAL_WS_RE = re.compile(r"[^\S\n]+")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def normalize_text(text: str) -> str:
    """Apply deterministic cleaning rules to ``text``."""
    text = _CRLF_RE.sub("\n", text)
    text = _CONTROL_RE.sub("", text)
    text = _HORIZONTAL_WS_RE.sub(" ", text)
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(line for line in lines if line)
    return text.strip()


class CleaningStage(Stage):
    """Normalizes parsed content deterministically."""

    def execute(self, context: IngestionContext) -> IngestionContext:
        if context.parsed_content is None:
            raise ValueError("CleaningStage requires parsed content")
        context.cleaned_content = normalize_text(context.parsed_content)
        return context