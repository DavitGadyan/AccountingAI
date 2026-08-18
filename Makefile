.PHONY: help install up down migrate seed api worker web test test-backend test-frontend lint build

help:
	@grep -E '^[a-zA-Z-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Install backend and frontend dependencies
	cd backend && python3 -m pip install -e ".[dev]"
	cd frontend && npm install

up: ## Start Postgres, Redis and MinIO
	docker compose up -d

down: ## Stop the local stack
	docker compose down

migrate: ## Apply database migrations
	cd backend && alembic upgrade head

seed: ## Load the reference engagement — 2 holdcos, 5 syndications, 2 tax years
	cd backend && python3 scripts/seed_demo.py

api: ## Run the API on :8000
	cd backend && uvicorn app.main:app --reload --port 8000

worker: ## Run the extraction worker
	cd backend && arq app.workers.tasks.WorkerSettings

web: ## Run the frontend on :3000
	cd frontend && npm run dev

test: test-backend test-frontend ## Run every test — no network, no database, no API key

test-backend: ## Rules, workpapers, filing gate, completeness, tie-out
	cd backend && python3 -m pytest -q

test-frontend: ## Architecture graph integrity and tour narrative
	cd frontend && npx vitest run

lint: ## Lint and typecheck both sides
	cd backend && ruff check app tests
	cd frontend && npx tsc --noEmit

build: ## Production build of the frontend
	cd frontend && npm run build
