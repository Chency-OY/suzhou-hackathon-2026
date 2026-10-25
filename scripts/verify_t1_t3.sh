#!/usr/bin/env bash
set -euo pipefail
missing=0
for f in AGENTS.md SPEC.md Makefile pyproject.toml .env.example .gitignore scripts/ci.sh \
  docs/PROGRESS.md docs/QUESTIONS.md prompts/CHANGELOG.md prompts/_example.md \
  backend/app/main.py backend/app/config.py backend/app/db.py \
  backend/app/models/constants.py backend/app/models/domain.py \
  backend/app/llm/provider.py backend/app/llm/mock.py backend/app/llm/openai_compat.py \
  backend/app/llm/factory.py backend/app/llm/structured.py backend/app/llm/usage.py \
  backend/app/llm/prompts.py backend/tests/test_models.py backend/tests/test_db.py \
  backend/tests/test_llm.py backend/tests/test_prompts.py backend/tests/test_health.py; do
  [ -f "$f" ] || { echo "MISSING: $f"; missing=1; }
done
[ "$missing" = 0 ] || exit 1
make lint
make test
. .venv/bin/activate
python - <<'PY'
import sys; sys.path.insert(0, "backend")
from app.models import DoctorPersona, Scenario, Session, Report, PlaybookCard, DoctorState, Turn, Finding
from app.llm import get_provider, MockLLM, structured_call, load_prompt, UsageTracker
from app.db import Repo
print("imports OK; provider =", get_provider().name)
PY
echo "T1-T3 VERIFIED"
