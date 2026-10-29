#!/usr/bin/env bash
# 在【有外网的开发机】上，为【无外网的服务器】预先下载依赖包到 wheelhouse/。
# 用法：bash scripts/build_wheelhouse.sh        （服务器为 Python 3.12 + x86_64 Linux；不同请用环境变量覆盖）
set -euo pipefail
cd "$(dirname "$0")/.."
PYV="${SERVER_PY:-3.12}"
ABI="cp${PYV/./}"
python3 scripts/extract_requirements.py --extras rag > /tmp/rep_trainer_req.txt
rm -rf wheelhouse && mkdir wheelhouse
pip download -r /tmp/rep_trainer_req.txt -d wheelhouse --only-binary=:all: \
  --python-version "$PYV" --implementation cp --abi "$ABI" \
  --platform manylinux2014_x86_64 --platform manylinux_2_17_x86_64 --platform manylinux_2_28_x86_64 \
  --platform manylinux_2_27_x86_64 --platform manylinux_2_34_x86_64 --platform linux_x86_64
echo "已下载 $(ls wheelhouse | wc -l) 个文件到 wheelhouse/（$(du -sh wheelhouse | cut -f1)）"
