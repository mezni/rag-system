.PHONY: up down ps logs db-shell

up:
	docker compose up -d

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f postgres

db-shell:
	docker compose exec postgres psql -U rag -d rag_system -h localhost -p 5432