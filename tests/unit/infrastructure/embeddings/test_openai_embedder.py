from src.infrastructure.embeddings.openai_embedder import OpenAIEmbedder


class _FakeEmbeddingItem:
    def __init__(self, index: int, embedding: list[float]) -> None:
        self.index = index
        self.embedding = embedding


class _FakeEmbeddingsResponse:
    def __init__(self, items: list[_FakeEmbeddingItem]) -> None:
        self.data = items


class _FakeEmbeddingsApi:
    def __init__(self, items: list[_FakeEmbeddingItem]) -> None:
        self._items = items
        self.model: str | None = None
        self.input: list[str] | None = None

    def create(self, *, model: str, input: list[str]) -> _FakeEmbeddingsResponse:
        self.model = model
        self.input = input
        return _FakeEmbeddingsResponse(self._items)


class _FakeClient:
    def __init__(self, items: list[_FakeEmbeddingItem]) -> None:
        self.embeddings = _FakeEmbeddingsApi(items)


def test_openai_embedder_returns_ordered_vectors() -> None:
    embedder = OpenAIEmbedder(
        client=_FakeClient(
            [
                _FakeEmbeddingItem(index=1, embedding=[0.3, 0.4]),
                _FakeEmbeddingItem(index=0, embedding=[0.1, 0.2]),
            ]
        )
    )

    assert embedder.embed(["a", "b"]) == [[0.1, 0.2], [0.3, 0.4]]


def test_openai_embedder_sends_all_texts_and_model() -> None:
    client = _FakeClient([_FakeEmbeddingItem(index=i, embedding=[float(i)]) for i in range(2)])

    OpenAIEmbedder(client=client, model="text-embedding-3-large").embed(["x", "y"])

    assert client.embeddings.input == ["x", "y"]
    assert client.embeddings.model == "text-embedding-3-large"


def test_openai_embedder_empty_input() -> None:
    client = _FakeClient([])

    assert OpenAIEmbedder(client=client).embed([]) == []