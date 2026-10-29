#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Ubuntu 无 python3-venv 包且无 sudo 时，回退到用户级安装的 virtualenv（见 docs/QUESTIONS.md）
if [ ! -d .venv ]; then
  python3 -m venv .venv 2>/dev/null || python3 -m virtualenv .venv
fi
. .venv/bin/activate
# 依赖安装：优先离线 wheelhouse（服务器无外网），其次在线；都失败则沿用现有环境并明确告警
if ls wheelhouse/*.whl >/dev/null 2>&1; then
  python scripts/extract_requirements.py --extras rag > /tmp/rep_trainer_req.txt
  pip install --no-index --find-links wheelhouse -r /tmp/rep_trainer_req.txt \
    || echo "警告：离线安装失败，沿用现有依赖"
elif ! pip install -q -e ".[dev,rag]"; then
  echo "警告：没有 wheelhouse 且在线安装失败，沿用现有依赖（如新增了依赖，服务可能起不来）"
fi
if [ -f frontend/package.json ] && command -v pnpm >/dev/null && [ ! -f frontend/dist/index.html -o "${REBUILD_WEB:-1}" = "1" ]; then
  (cd frontend && pnpm install --frozen-lockfile && pnpm build)
fi
[ -f frontend/dist/index.html ] || { echo "缺少 frontend/dist（请在本地构建后上传，见 docs/DEPLOY.md）"; exit 1; }
python scripts/seed.py
bash scripts/run_prod.sh restart
BASE="http://127.0.0.1:${PORT:-8000}" bash scripts/healthcheck.sh
