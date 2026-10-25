#!/usr/bin/env bash
set -euo pipefail
SERVER="${SERVER:-sutai}"
REMOTE_DIR="${REMOTE_DIR:-~/rep-trainer}"
cd "$(dirname "$0")/.."
ssh "$SERVER" "mkdir -p $REMOTE_DIR"
rsync -az --delete \
  --exclude '.git/' --exclude '.venv/' --exclude 'node_modules/' --exclude '.env' --exclude '.env.server' \
  --exclude 'data/app.db' --exclude 'data/chroma/' --exclude 'data/usage/' \
  --exclude 'run/' --exclude 'logs/' --exclude '__pycache__/' --exclude '.pytest_cache/' --exclude '.ruff_cache/' \
  ./ "$SERVER:$REMOTE_DIR/"
# 首次部署：生成服务器 .env（若已存在则不覆盖）
ssh "$SERVER" "cd $REMOTE_DIR && [ -f .env ] || cp deploy/env.server.example .env"
ssh "$SERVER" "cd $REMOTE_DIR && bash scripts/deploy.sh"
