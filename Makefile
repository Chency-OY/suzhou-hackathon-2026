.PHONY: setup dev test lint build-facts seed gen-personas gen-scenarios gen-scenarios-v2 review web-build deploy healthcheck apply-review sim
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
	@if [ -f frontend/package.json ]; then cd frontend && pnpm exec tsc --noEmit && pnpm exec vitest run; fi

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

gen-scenarios-v2:
	$(VENV) && python scripts/gen_scenarios_v2.py

review:
	$(VENV) && python scripts/export_review.py

web-build:
	cd frontend && pnpm install && pnpm build

deploy:
	bash scripts/push_to_server.sh

healthcheck:
	bash scripts/healthcheck.sh

apply-review:
	$(VENV) && python scripts/apply_review.py && python scripts/seed.py

sim:
	$(VENV) && python scripts/sim_session.py
