#!/usr/bin/env bash
# 一键真实生成 + 总验收。前提：在 .env 填好 LLM_API_KEY（其余项已配好）。
# 用法：bash scripts/run_real_gen.sh
# 若画像不足 30：python scripts/gen_personas.py --target 40 --candidates 450 后重跑本脚本后半段。
set -euo pipefail
cd "$(dirname "$0")/.."

if ! grep -Eq '^LLM_API_KEY=..+' .env; then
  echo "请先在 .env 中填入 LLM_API_KEY（智谱开放平台 bigmodel.cn 的 API Key）。"
  exit 2
fi

. .venv/bin/activate

echo "=== 1/6 真实模型冒烟 ==="
python scripts/llm_smoke.py

echo "=== 2/6 生成医生画像（目标 40，候选 300）==="
python scripts/gen_personas.py --target 40

echo "=== 3/6 重建知识库并导入数据 ==="
python scripts/seed.py

echo "=== 4/6 生成场景 ==="
python scripts/gen_scenarios.py

echo "=== 5/6 导出人工抽检清单 ==="
python scripts/export_review.py

echo "=== 6/6 严格总验收（画像>=30 / 场景>=36）==="
STRICT=1 bash scripts/verify_t4_t7.sh

echo
echo "完成。请人工阅读 docs/REVIEW_SAMPLE.md 抽检；token 用量见 data/usage/*.jsonl。"
