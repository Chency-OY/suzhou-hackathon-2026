#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Ubuntu 无 python3-venv 包且无 sudo 时，回退到用户级安装的 virtualenv（见 docs/QUESTIONS.md）
if [ ! -d .venv ]; then
  python3 -m venv .venv 2>/dev/null || python3 -m virtualenv .venv
fi
. .venv/bin/activate
pip install -q -U pip && pip install -q -e ".[dev,rag]"
if [ -f frontend/package.json ] && command -v pnpm >/dev/null && [ ! -f frontend/dist/index.html -o "${REBUILD_WEB:-1}" = "1" ]; then
  (cd frontend && pnpm install --frozen-lockfile && pnpm build)
fi
[ -f frontend/dist/index.html ] || { echo "缺少 frontend/dist（请在本地构建后上传，见 docs/DEPLOY.md）"; exit 1; }
python scripts/seed.py
bash scripts/run_prod.sh restart
BASE="http://127.0.0.1:${PORT:-8000}" bash scripts/healthcheck.sh
