# Getting Started

## Prerequisites

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/)

## Install

```bash
uv sync --all-groups
```

## Activate the environment

```bash
source .venv/bin/activate
```

## Add a dependency

```bash
uv add <package>
```

## Run a script

```bash
uv run python -c "print('hello')"
```