#!/bin/bash
set -e

echo "Running database migrations"
alembic upgrade head

echo "Running ingestion pipeline"
exec python -m src.ingestion.pipeline --source-dir /rag-system/data/raw/