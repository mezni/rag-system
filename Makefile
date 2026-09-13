.PHONY: help init db migrations run ui test lint

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "} {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

init: ## Initialize the project (install deps, setup db, run migrations)
	uv sync
	docker compose up -d db
	@sleep 3
	uv run alembic upgrade head
	@echo "Project initialized!"

db: ## Start database container
	docker compose up -d db

migrations: ## Create new Alembic migration
	uv run alembic revision --autogenerate -m "$(msg)"

run: ## Run the ingestion pipeline
	uv run src/ingestion/pipeline.py

ui: ## Run the Streamlit ops dashboard
	PYTHONPATH=. uv run streamlit run src/ui/app.py

test: ## Run tests
	uv run pytest

lint: ## Run linting
	uv run ruff check src/