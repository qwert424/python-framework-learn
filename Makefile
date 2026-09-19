# Makefile

export PYTHONDONTWRITEBYTECODE := 1

.PHONY: dev debug sync

dev:
	uv run --package web-service fastapi dev apps/web-service/app/main.py --port 8080

debug:
	uv run --package web-service python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m fastapi dev apps/web-service/app/main.py --port 8000

sync:
	uv sync --all-packages --all-groups