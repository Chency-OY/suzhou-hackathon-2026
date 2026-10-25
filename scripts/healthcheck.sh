#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8000}"
curl -fsS "$BASE/api/health"; echo
n=$(curl -fsS "$BASE/api/scenarios" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
echo "scenarios: $n"; [ "$n" -gt 0 ]
curl -fsS "$BASE/" | grep -q 'id="root"' && echo "frontend OK"
