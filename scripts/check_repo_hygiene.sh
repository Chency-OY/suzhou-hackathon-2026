#!/usr/bin/env bash
# 检查不该进仓库的文件是否被 git 跟踪。有问题返回 1。
cd "$(dirname "$0")/.." || exit 1
PATTERN='(^|/)(_tmp_[^/]+|Makefile[A-Za-z0-9]{6}|[^/]+\.egg-info|\.env|\.venv|node_modules|__pycache__|\.pytest_cache|\.ruff_cache)(/|$)|(^|/)data/(app\.db|chroma|usage)(/|$)|(^|/)frontend/dist(/|$)|(^|/)wheelhouse(/|$)'
bad=$(git ls-files | grep -E "$PATTERN" || true)
if [ -n "$bad" ]; then
  echo "以下文件被 git 跟踪，不应入库："
  echo "$bad" | head -40
  exit 1
fi
if git ls-files --error-unmatch .env >/dev/null 2>&1; then
  echo "严重：.env 被跟踪，里面可能有密钥"
  exit 1
fi
echo "仓库清洁：没有发现不该入库的文件"
