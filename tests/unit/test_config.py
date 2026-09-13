from src.ingestion.config import Settings


def test_defaults():
    settings = Settings()

    assert settings.embedding_provider == "hf"
    assert settings.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
    assert settings.embedding_dim == 384
    assert settings.chunk_size_chars == 1500
    assert settings.chunk_overlap_chars == 200
    assert settings.chunking_strategy == "semantic"
    assert settings.environment == "development" or settings.environment


def test_supported_extensions_include_unstructured_formats():
    settings = Settings()
    for ext in (".pdf", ".md", ".txt", ".docx", ".html", ".csv", ".xlsx", ".pptx", ".json"):
        assert ext in settings.supported_extensions


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("CHUNK_SIZE_CHARS", "900")
    monkeypatch.setenv("CHUNK_OVERLAP_CHARS", "100")
    monkeypatch.setenv("CHUNKING_STRATEGY", "fixed")

    settings = Settings()

    assert settings.chunk_size_chars == 900
    assert settings.chunk_overlap_chars == 100
    assert settings.chunking_strategy == "fixed"