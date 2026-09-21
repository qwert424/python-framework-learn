# Makefile

export PYTHONDONTWRITEBYTECODE := 1

.PHONY: dev debug sync db-up db-down db-verify db-shell db-reset db-migrate db-upgrade db-downgrade test test-unit test-integration test-e2e test-smoke coverage coverage-html

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
	uv run --package web-service alembic -c apps/web-service/alembic.ini revision --autogenerate -m "$(or $(message),auto migration)"

db-upgrade:
	uv run --package web-service alembic -c apps/web-service/alembic.ini upgrade head

db-downgrade:
	uv run --package web-service alembic -c apps/web-service/alembic.ini downgrade $(version)

test:
	uv run pytest packages/common-utils/test/unit/ apps/web-service/test/unit/ apps/web-service/test/integration/ -q --cov=app --cov=common_utils --cov-report=term-missing --cov-fail-under=80

test-unit:
	uv run pytest packages/common-utils/test/unit/ apps/web-service/test/unit/ -q

test-integration:
	uv run pytest packages/common-utils/test/integration/ apps/web-service/test/integration/ -q

test-e2e:
	uv run pytest apps/web-service/test/e2e/ -q

test-smoke:
	uv run pytest apps/web-service/test/e2e/ -q -m smoke
	uv run pytest packages/common-utils/test/unit/ apps/web-service/test/unit/ apps/web-service/test/integration/ -q -m smoke

coverage:
	uv run --package web-service coverage run --source=app -m pytest apps/web-service/test/unit/ apps/web-service/test/integration/ -q
	uv run --package web-service coverage report

coverage-html:
	uv run --package web-service coverage run --source=app -m pytest apps/web-service/test/unit/ apps/web-service/test/integration/ -q
	uv run --package web-service coverage html