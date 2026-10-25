"""从上游结构化事实库（data/sources/facts_upstream.yaml）机械抽取，生成
data/kb/facts.yaml（SPEC 4.4 的扁平条目格式，供 RAG 入库）。

原则：
- 上游文件逐字保留，本脚本只读取；
- statement 由上游 value/quote/metric/rows 等字段机械拼接，不引入任何外部医学知识、
  不换算、不四舍五入；
- verified 严格等于上游 status == "verified"；partial/unverified 在 caution 中注明；
- status == "deprecated"（已废止）与 discrepancies/法规/合规规则不入知识库（见 QUESTIONS）。
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml

UPSTREAM = Path("data/sources/facts_upstream.yaml")
OUT = Path("data/kb/facts.yaml")

# 只抽取医生问诊/场景可能用到的医学与产品事实；法规、合规规则、冲突清单等
# 属于合规引擎（后续任务），不进 RAG 知识库。
INCLUDE_SECTIONS = [
    "product", "indications", "dosing", "contraindications", "boxed_warning", "key_warnings",
    "safety", "pk", "efficacy", "competitor", "guidelines", "trials_bibliography",
]

# id 前缀 -> SPEC 4.4 标准类目（guide 为非标准类目，check_facts 会告警，见 QUESTIONS）
CATEGORY_RULES: list[tuple[str, str]] = [
    ("label.indication", "indication"),
    ("label.warning", "safety"),
    ("label.contraindication", "safety"),
    ("label.", "indication"),
    ("product.", "company"),
    ("dose.", "dosing"),
    ("pk.", "dosing"),
    ("safety.", "safety"),
    ("efficacy.", "efficacy"),
    ("trial.", "efficacy"),
    ("competitor.", "competitor"),
    ("guide.", "guide"),
]

# 构造 statement 时跳过的元数据键（quote 单独处理）
META_KEYS = {"id", "status", "evidence", "source", "source_url", "source_refs",
             "corroborated_by", "column_order", "footnote", "urls", "accessed"}

# caution 候选键（按序拼接全部非空项）
CAUTION_KEYS = ["caution", "citation_rule", "compliance_note", "interpretation",
                "rule", "warning", "reason", "note", "caveat"]


def category_of(fid: str) -> str | None:
    for prefix, cat in CATEGORY_RULES:
        if fid.startswith(prefix):
            return cat
    return None


def has_own_fact(x) -> bool:
    """子结构内是否还有独立 id 的事实节点（有则由递归单独产出，父节点不重复拼接）。"""
    if isinstance(x, dict):
        nid = x.get("id")
        if isinstance(nid, str) and "." in nid and category_of(nid):
            return True
        return any(has_own_fact(v) for v in x.values())
    if isinstance(x, list):
        return any(has_own_fact(i) for i in x)
    return False


def fmt(v, unit: str | None = None) -> str:
    if isinstance(v, bool):
        return "是" if v else "否"
    if isinstance(v, (int, float)):
        s = repr(v) if isinstance(v, float) else str(v)
        if unit:
            return f"{s}{unit}" if unit == "%" else f"{s} {unit}"
        return s
    if isinstance(v, list):
        return "、".join(fmt(x, unit) for x in v)
    if isinstance(v, dict):
        if "values" in v or "quote" in v:
            return build_statement(v, None, None)
        return "；".join(f"{k}：{fmt(x)}" for k, x in v.items())
    return str(v)


def build_statement(node: dict, columns: list | None, unit: str | None) -> str:
    # 表格行：拼成「指标：列名 值、列名 值」
    if "values" in node:
        label = node.get("metric") or node.get("ae") or node.get("topic") or ""
        vals = node["values"]
        if columns and len(columns) == len(vals):
            body = "、".join(f"{c} {fmt(v, unit or '')}".strip() for c, v in zip(columns, vals))
        else:
            body = fmt(vals, unit)
        extra = []
        if node.get("ci"):
            extra.append(f"95%CI {fmt(node['ci'])}")
        if node.get("diff") is not None:
            extra.append(f"组间差 {fmt(node['diff'], unit)}")
        if node.get("p") is not None:
            extra.append(f"P {fmt(node['p'])}")
        s = (f"{label}：" if label else "") + body
        if extra:
            s += "（" + "；".join(extra) + "）"
        return s
    # 通用：自身标量 + 无独立 id 的子结构；quote 逐字附后
    parts: list[str] = []
    for k, v in node.items():
        if k in META_KEYS or k == "quote":
            continue
        if isinstance(v, (dict, list)):
            if has_own_fact(v):
                continue
            parts.append(f"{k}：{fmt(v)}" if k != "value" else fmt(v))
        else:
            parts.append(fmt(v, unit) if k == "value" else fmt(v))
    quote = (node.get("quote") or "").strip()
    if quote:
        parts.append("原文：「" + quote + "」")
    return "；".join(p for p in parts if p and p.strip())


def walk(x, columns: list | None, unit: str | None, facts: list[dict], seen: set[str],
         skipped: Counter) -> None:
    if isinstance(x, dict):
        columns = x.get("column_order") or x.get("columns") or columns
        unit = x.get("unit") or unit
        nid = x.get("id")
        if isinstance(nid, str) and "." in nid and category_of(nid):
            emit(x, columns, unit, facts, seen, skipped)
        for v in x.values():
            if v is x.get("column_order"):
                continue
            walk(v, columns, unit, facts, seen, skipped)
    elif isinstance(x, list):
        for it in x:
            walk(it, columns, unit, facts, seen, skipped)


def emit(node: dict, columns: list | None, unit: str | None, facts: list[dict],
         seen: set[str], skipped: Counter) -> None:
    fid = node["id"]
    if fid in seen:
        skipped["重复 id 跳过"] += 1
        return
    if node.get("status") == "deprecated":
        skipped["deprecated 跳过"] += 1
        return
    statement = build_statement(node, columns, unit).strip()
    if len(statement) < 5:
        skipped["纯容器节点跳过"] += 1
        return  # 数据都在子条目里，由子条目承载
    status = str(node.get("status") or "")
    cautions = [str(node[k]).strip() for k in CAUTION_KEYS
                if node.get(k) and isinstance(node.get(k), str)]
    if status == "partial":
        cautions.append("上游核验状态 partial（部分核验，引用前复核）")
    elif status == "unverified":
        cautions.append("上游核验状态 unverified（未核验，引用前必须复核）")
    source = node.get("source") or "；".join(node.get("source_refs") or []) \
        or (f"上游事实库[{node.get('evidence')}]" if node.get("evidence") else "上游事实库 facts_upstream.yaml")
    seen.add(fid)
    facts.append({
        "id": fid,
        "category": category_of(fid),
        "statement": statement,
        "source": source,
        "source_url": node.get("source_url") or "",
        "verified": status == "verified",
        "caution": "；".join(c for c in cautions if c),
    })


def main() -> int:
    data = yaml.safe_load(UPSTREAM.read_text(encoding="utf-8"))
    facts: list[dict] = []
    seen: set[str] = set()
    skipped: Counter = Counter()
    for section in INCLUDE_SECTIONS:
        walk(data.get(section), None, None, facts, seen, skipped)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(yaml.safe_dump(facts, allow_unicode=True, sort_keys=False, width=9999),
                   encoding="utf-8")
    cats = Counter(f["category"] for f in facts)
    ver = sum(f["verified"] for f in facts)
    print(f"生成 {len(facts)} 条事实（已核验 {ver}）-> {OUT}")
    print("按类目：", dict(sorted(cats.items())))
    if skipped:
        print("跳过统计：", dict(skipped))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
