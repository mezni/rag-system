"""Configuration for the ingestion pipeline."""

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    embedding_provider: str = Field(default="hf", alias="EMBEDDING_PROVIDER")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", alias="EMBEDDING_MODEL")
    embedding_dim: int = Field(default=384, alias="EMBEDDING_DIM")
    embedding_batch_size: int = Field(default=64, alias="EMBEDDING_BATCH_SIZE")

    chunk_size_chars: int = Field(default=1500, alias="CHUNK_SIZE_CHARS")
    chunk_overlap_chars: int = Field(default=200, alias="CHUNK_OVERLAP_CHARS")

    supported_extensions: tuple[str, ...] = (".pdf", ".md", ".txt")

    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    hf_token: str | None = Field(default=None, alias="HF_TOKEN")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    class Config:
        env_file = ".env"
        populate_by_name = True