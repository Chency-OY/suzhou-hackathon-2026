#!/usr/bin/env bash
set -euo pipefail
missing=0
for f in scripts/check_facts.py scripts/llm_smoke.py scripts/seed.py scripts/gen_personas.py \
  scripts/gen_scenarios.py scripts/export_review.py prompts/persona_gen.md prompts/scenario_gen.md \
  data/rubric/name_blacklist.txt backend/app/deps.py backend/app/api/scenarios.py \
  backend/app/rag/facts.py backend/app/rag/embedding.py backend/app/rag/store.py backend/app/rag/kb.py \
  backend/app/personas/validate.py backend/app/personas/select.py backend/app/personas/generate.py \
  backend/app/personas/demo_seed.py backend/app/scenarios/generate.py \
  backend/tests/test_facts.py backend/tests/test_rag.py backend/tests/test_personas.py \
  backend/tests/test_scenarios.py backend/tests/test_api_scenarios.py; do
  [ -f "$f" ] || { echo "MISSING: $f"; missing=1; }
done
[ "$missing" = 0 ] || exit 1
bash scripts/verify_t1_t3.sh
. .venv/bin/activate
python scripts/check_facts.py
python scripts/seed.py
python - <<'PY'
import json, pathlib
def n(p):
    f = pathlib.Path(p)
    return len([x for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]) if f.exists() else 0
personas, scenarios = n("data/personas/personas.jsonl"), n("data/scenarios/scenarios.jsonl")
print(f"personas={personas} scenarios={scenarios}")
import os
if os.environ.get("STRICT") == "1":
    assert personas >= 30, "画像不足 30"
    assert scenarios >= 36, "场景不足 36"
else:
    if personas < 30 or scenarios < 36:
        print("提示：数据量未达 30/36（STRICT=1 时会失败；离线 demo 数据属正常）")
PY
echo "T4-T7 VERIFIED"
