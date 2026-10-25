.PHONY: setup dev test lint build-facts seed gen-personas gen-scenarios review
PY ?= python3
VENV = . .venv/bin/activate

setup:
	$(PY) -m venv .venv
	$(VENV) && pip install -U pip && pip install -e ".[dev,rag]"
	@if [ -f frontend/package.json ]; then cd frontend && pnpm install; fi

dev:
	$(VENV) && uvicorn app.main:app --app-dir backend --reload --port 8000

test:
	$(VENV) && pytest -q
	@if [ -f frontend/package.json ]; then cd frontend && pnpm exec tsc --noEmit; fi

lint:
	$(VENV) && ruff check backend

build-facts:
	$(VENV) && python scripts/build_facts.py

seed:
	$(VENV) && python scripts/seed.py

gen-personas:
	$(VENV) && python scripts/gen_personas.py --target $(or $(N),40)

gen-scenarios:
	$(VENV) && python scripts/gen_scenarios.py

review:
	$(VENV) && python scripts/export_review.py
