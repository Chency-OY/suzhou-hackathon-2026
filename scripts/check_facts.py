"""校验 data/kb/facts.yaml 并生成 docs/FACTS_REPORT.md。
默认只读。--fix 仅为缺失字段补默认值（source/source_url/caution 为空串，verified 为 false），
不改写 statement；修改前会备份为 facts.yaml.bak。"""
import argparse
import shutil
import sys
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, "backend")
from app.rag.facts import load_facts, read_raw  # noqa: E402

PATH = Path("data/kb/facts.yaml")
STD_CATEGORIES = {"efficacy", "safety", "dosing", "indication", "competitor", "access", "company"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true")
    args = ap.parse_args()
    if not PATH.exists():
        print(f"找不到 {PATH}。请把 facts.yaml 放到该路径。")
        return 2

    if args.fix:
        raw = read_raw(PATH)
        shutil.copy(PATH, PATH.with_suffix(".yaml.bak"))
        for it in raw:
            if isinstance(it, dict):
                it.setdefault("source", "")
                it.setdefault("source_url", "")
                it.setdefault("verified", False)
                it.setdefault("caution", "")
        PATH.write_text(yaml.safe_dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8")

    facts, errors = load_facts(PATH)
    warnings: list[str] = []
    for f in facts:
        if f.category not in STD_CATEGORIES:
            warnings.append(f"{f.id}: 非标准 category「{f.category}」")
        if not f.source:
            warnings.append(f"{f.id}: 缺少 source")
    cat = Counter(f.category for f in facts)
    ver = Counter("已核验" if f.verified else "未核验" for f in facts)

    lines = ["# facts.yaml 检查报告", "", f"- 合法条目：{len(facts)}", f"- 错误：{len(errors)}",
             f"- 警告：{len(warnings)}", "", "## 按类别", ""]
    lines += [f"- {k}: {v}" for k, v in sorted(cat.items())]
    lines += ["", "## 核验状态", ""] + [f"- {k}: {v}" for k, v in ver.items()]
    lines += ["", "## 错误", ""] + ([f"- {e}" for e in errors] or ["- 无"])
    lines += ["", "## 警告", ""] + ([f"- {w}" for w in warnings] or ["- 无"])
    Path("docs").mkdir(exist_ok=True)
    Path("docs/FACTS_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"facts: {len(facts)} 条合法, {len(errors)} 错误, {len(warnings)} 警告 -> docs/FACTS_REPORT.md")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
