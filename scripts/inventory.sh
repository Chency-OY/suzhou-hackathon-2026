#!/usr/bin/env bash
# 生成 docs/STATE.md：项目现状快照（给人和 AI 助手看，省得它们自己翻目录）
# 用法：bash scripts/inventory.sh [--with-tests]
# 只读脚本：不修改任何代码和数据；不会打印任何密钥内容（只列出疑似文件名）。
cd "$(dirname "$0")/.." || exit 1
OUT=docs/STATE.md
mkdir -p docs
PYBIN=python3
[ -x .venv/bin/python ] && PYBIN=.venv/bin/python

{
echo "# 项目现状快照（自动生成，勿手改）"
echo
echo "- 生成时间：$(date '+%F %T')"
echo "- 分支：$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 无)　最近提交：$(git log -1 --format='%h %s' 2>/dev/null || echo 无)"
echo "- 冻结文件校验（SPEC.md / AGENTS.md 的哈希前 12 位）：$(sha256sum SPEC.md AGENTS.md 2>/dev/null | cut -c1-12 | tr '\n' ' ')"

echo; echo "## 最近 15 次提交"; echo '```'
git log --oneline -15 2>/dev/null; echo '```'

echo; echo "## 未提交改动"; echo '```'
git status --short 2>/dev/null | head -30; echo '```'

echo; echo "## 目录树（深度 3）"; echo '```'
find . -maxdepth 3 \( -name .git -o -name .venv -o -name node_modules -o -name __pycache__ -o -name chroma \
  -o -name dist -o -name .pytest_cache -o -name .ruff_cache -o -name usage \) -prune -o -print | sort | head -220
echo '```'

echo; echo "## 代码规模（行数）"; echo '```'
for d in backend/app backend/tests frontend/src scripts prompts; do
  if [ -d "$d" ]; then
    n=$(find "$d" -type f \( -name '*.py' -o -name '*.ts' -o -name '*.tsx' -o -name '*.md' -o -name '*.sh' -o -name '*.yaml' \) \
        -not -path '*/node_modules/*' -print0 | xargs -0 cat 2>/dev/null | wc -l)
    printf '%-16s %s 行\n' "$d" "$n"
  fi
done
echo '```'

echo; echo "## Makefile 目标"; echo '```'
[ -f Makefile ] && grep -E '^[a-zA-Z0-9_-]+:' Makefile | cut -d: -f1 | tr '\n' ' ' || echo 无 Makefile
echo; echo '```'

echo; echo "## 提示词与版本"; echo '```'
for f in prompts/*.md; do [ -f "$f" ] && printf '%-28s %s\n' "$(basename "$f")" "$(grep -m1 '^version:' "$f")"; done
echo '```'

echo; echo "## 后端接口"; echo '```'
grep -rnE '@(router|app)\.(get|post|put|delete)' backend/app 2>/dev/null | sed -E 's/^([^:]+):([0-9]+):\s*/\1 L\2  /' | head -60
echo '```'

echo; echo "## 前端路由"; echo '```'
grep -nE 'path=|index' frontend/src/App.tsx 2>/dev/null | head -30
echo '```'

echo; echo "## 数据概况"; echo '```'
$PYBIN - <<'PY'
import json, pathlib, collections
try:
    import yaml
except ImportError:
    yaml = None

def jl(p):
    f = pathlib.Path(p)
    if not f.exists():
        return None
    return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]

f = pathlib.Path("data/kb/facts.yaml")
if f.exists() and yaml:
    d = yaml.safe_load(f.read_text(encoding="utf-8"))
    d = d.get("facts", d) if isinstance(d, dict) else d
    d = [x for x in d if isinstance(x, dict)]
    v = sum(1 for x in d if x.get("verified") is True)
    print(f"facts：{len(d)} 条，已核验 {v} 条；类别 {dict(collections.Counter(x.get('category') for x in d))}")
else:
    print("facts：未找到 data/kb/facts.yaml（或缺少 pyyaml）")

P = jl("data/personas/personas.jsonl")
if P is None:
    print("画像：未找到")
else:
    print(f"画像：{len(P)} 个；科室×难度 {dict(collections.Counter(p['department'] + '/' + p['difficulty'] for p in P))}")

S = jl("data/scenarios/scenarios.jsonl")
if S is None:
    print("场景：未找到")
else:
    dept = {p["id"]: p["department"] for p in (P or [])}
    print(f"场景：{len(S)} 个；类型 {dict(collections.Counter(s['type'] for s in S))}")
    print(f"      科室 {dict(collections.Counter(dept.get(s['persona_id'], '?') for s in S))}")

r = pathlib.Path("data/scenarios/review.json")
if r.exists() and r.read_text(encoding='utf-8').strip():
    rv = json.loads(r.read_text(encoding="utf-8"))
    print(f"审核状态：{dict(collections.Counter(v.get('status') for v in rv.values()))}")
else:
    print("审核状态：review.json 不存在或为空")
print("预筛结果：", "有" if pathlib.Path("data/scenarios/prescreen.json").exists() else "无")
print("label.md：", "有" if pathlib.Path("data/sources/label.md").exists() else "无")
print("data/ 下的子目录与文件：", sorted(p.name for p in pathlib.Path("data").iterdir() if p.name not in ("chroma", "usage", "app.db")) if pathlib.Path("data").exists() else "无")
PY
echo '```'

echo; echo "## TODO / FIXME（前 20 条）"; echo '```'
grep -rIn 'TODO\|FIXME' backend frontend/src scripts --exclude=inventory.sh 2>/dev/null | grep -v node_modules | head -20
echo '```'

echo; echo "## 疑似密钥文件（只列文件名，不显示内容）"; echo '```'
grep -rIlE '(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9_]*API_KEY *= *[A-Za-z0-9._-]{16,})' . \
  --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv --exclude=.env.example --exclude=STATE.md 2>/dev/null | head -10
echo '（空表示未发现；若列出了 .env，确认它没有被提交）'; echo '```'

echo; echo "## docs/PROGRESS.md 末 15 行"; echo '```'
tail -15 docs/PROGRESS.md 2>/dev/null; echo '```'
echo; echo "## docs/QUESTIONS.md 末 12 行"; echo '```'
tail -12 docs/QUESTIONS.md 2>/dev/null; echo '```'

if [ "${1:-}" = "--with-tests" ]; then
  echo; echo "## make lint（末 8 行）"; echo '```'
  make lint 2>&1 | tail -8; echo '```'
  echo; echo "## make test（末 20 行）"; echo '```'
  make test 2>&1 | tail -20; echo '```'
fi
} > "$OUT" 2>&1

echo "已生成 $OUT（$(wc -l < "$OUT") 行）"
