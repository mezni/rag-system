"""Embedding abstraction for text to vector conversion."""

from abc import ABC, abstractmethod


class Embedder(ABC):
    """Converts text inputs into vector representations."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, preserving order."""
        raise NotImplementedError