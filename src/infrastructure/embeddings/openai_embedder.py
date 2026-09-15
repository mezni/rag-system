"""OpenAI embedding client."""

from openai import OpenAI

from src.infrastructure.embeddings.base import Embedder


class OpenAIEmbedder(Embedder):
    """Embeds text using the OpenAI Embeddings API."""

    def __init__(
        self, client: OpenAI | None = None, *, model: str = "text-embedding-3-small"
    ) -> None:
        self._client = client
        self._model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        client = self._client if self._client is not None else OpenAI()
        response = client.embeddings.create(model=self._model, input=texts)
        ordered = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in ordered]