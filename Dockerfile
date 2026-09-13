FROM python:3.13-slim

WORKDIR /rag-system

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY uv.lock pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copy source code
COPY src/ ./src/
COPY docker/ ./docker/
COPY alembic.ini ./

# Expose port
EXPOSE 8000

# Run migrations then the pipeline
CMD ["/bin/bash", "/rag-system/docker/entrypoint.sh"]