#!/usr/bin/env bash
set -euo pipefail
missing=0
for f in data/rubric/state_rules.yaml data/scenarios/review.json prompts/signal_judge.md prompts/doctor_reply.md \
  prompts/scenario_review.md backend/app/scenarios/review.py backend/app/sessions/rules.py \
  backend/app/sessions/state.py backend/app/sessions/engine.py backend/app/api/sessions.py \
  scripts/prescreen_scenarios.py scripts/export_review.py scripts/apply_review.py scripts/regen_scenarios.py \
  scripts/sim_session.py frontend/src/pages/SessionPage.tsx frontend/src/lib/rep.ts \
  backend/tests/test_review.py backend/tests/test_state.py backend/tests/test_engine.py \
  backend/tests/test_api_sessions.py; do
  [ -f "$f" ] || { echo "MISSING: $f"; missing=1; }
done
[ "$missing" = 0 ] || exit 1
bash scripts/verify_t4_t7.sh
make lint
make test
(cd frontend && pnpm build)
echo "T11-T15 VERIFIED"
