.PHONY: dev test lint format setup db-up db-down migrate

# --- Infrastructure ---
db-up:
	docker compose up -d

db-down:
	docker compose down

db-reset:
	docker compose down -v
	docker compose up -d

# --- Backend ---
api-setup:
	cd apps/api && pip install -r requirements.txt

api-dev:
	cd apps/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

api-test:
	cd apps/api && python -m pytest tests/ -v

api-lint:
	cd apps/api && ruff check .

api-format:
	cd apps/api && ruff format .

migrate:
	cd apps/api && alembic upgrade head

migrate-create:
	cd apps/api && alembic revision --autogenerate -m "$(msg)"

# --- Frontend ---
web-setup:
	cd apps/web && npm install

web-dev:
	cd apps/web && npm run dev

web-build:
	cd apps/web && npm run build

web-lint:
	cd apps/web && npm run lint

# --- All ---
setup: db-up api-setup web-setup migrate

dev:
	@echo "Run in separate terminals:"
	@echo "  make db-up"
	@echo "  make api-dev"
	@echo "  make web-dev"

test: api-test

lint: api-lint web-lint

format: api-format
