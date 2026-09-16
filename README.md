# rag-system

A RAG (Retrieval-Augmented Generation) system.

## Requirements

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync
cp .env.example .env
```

## Development

```bash
uv run pytest
uv run ruff check .
```

## Layout

- `config/profiles/` – JSON environment profiles
- `src/config/` – settings and profile loading
- `src/core/` – errors, ids, clock primitives
- `tests/unit/` – unit tests