# Makefile

export PYTHONDONTWRITEBYTECODE := 1

.PHONY: dev debug sync db-up db-down db-verify db-shell db-reset db-migrate db-upgrade db-downgrade

dev:
	uv run --package web-service fastapi dev apps/web-service/app/main.py --port 8080

debug:
	uv run --package web-service python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m fastapi dev apps/web-service/app/main.py --port 8000

sync:
	uv sync --all-packages --all-groups

db-up:
	docker compose up -d

db-down:
	docker compose down

db-verify:
	docker compose exec -T db psql -U admin -d learn_db -c "SELECT current_database(), current_user, version();"

db-shell:
	docker compose exec -it db psql -U admin -d learn_db

db-reset:
	docker compose exec -T db psql -U admin -d learn_db -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;"

db-migrate:
	uv run --package web-service alembic -c apps/web-service/alembic.ini revision --autogenerate -m "$(message)"

db-upgrade:
	uv run --package web-service alembic -c apps/web-service/alembic.ini upgrade head

db-downgrade:
	uv run --package web-service alembic -c apps/web-service/alembic.ini downgrade $(version)