# ChangeTrail — local dev helpers
# Copyright (c) 2026 cvemula1 — MIT License
# https://github.com/cvemula1/ChangeTrail

.PHONY: dev demo seed serve ui test lint up down clean help

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

dev: ## Start DB + seed + API with hot reload (local Python)
	docker compose up -d db
	@echo "Waiting for PostgreSQL..."
	@sleep 4
	python3 -m changetrail seed
	python3 -m changetrail serve --reload

demo: ## Print demo timeline to stdout (zero dependencies)
	python3 -m changetrail demo

seed: ## Seed demo events into the database
	python3 -m changetrail seed

serve: ## Start API server
	python3 -m changetrail serve

ui: ## Start UI dev server (needs npm install in ui/)
	cd ui && npm run dev

test: ## Run tests
	python3 -m pytest tests/ -v

lint: ## Run linter
	ruff check changetrail/ tests/

up: ## Start everything with Docker Compose (one command)
	docker compose up -d --build
	@echo "Waiting for API to be ready..."
	@sleep 5
	docker compose exec api python -m changetrail seed || true
	@echo ""
	@echo "  ChangeTrail is running!"
	@echo "  UI:       http://localhost:3000"
	@echo "  API:      http://localhost:8000/api/v1/changes"
	@echo "  Swagger:  http://localhost:8000/docs"
	@echo "  Health:   http://localhost:8000/health"
	@echo ""

down: ## Stop Docker Compose
	docker compose down

clean: ## Remove generated files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov dist build *.egg-info
