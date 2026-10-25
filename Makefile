.PHONY: setup dev test lint seed gen-personas
PY ?= python3
VENV = . .venv/bin/activate

setup:
	$(PY) -m venv .venv
	$(VENV) && pip install -U pip && pip install -e ".[dev]"
	@if [ -f frontend/package.json ]; then cd frontend && pnpm install; fi

dev:
	$(VENV) && uvicorn app.main:app --app-dir backend --reload --port 8000

test:
	$(VENV) && pytest -q
	@if [ -f frontend/package.json ]; then cd frontend && pnpm exec tsc --noEmit; fi

lint:
	$(VENV) && ruff check backend

seed:
	@echo "seed: 将在 T4 实现"

gen-personas:
	@echo "gen-personas: 将在 T5 实现 (N=$(N))"
