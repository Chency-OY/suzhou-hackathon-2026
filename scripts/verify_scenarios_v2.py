"""校验新场景集：数量、覆盖、泄露、数字、合规场景的陷阱与一票否决标记。"""
import re
import sys
from pathlib import Path

sys.path.insert(0, "backend")
from app.corpus import load_bank  # noqa: E402
from app.models import DoctorPersona, Scenario  # noqa: E402
from app.scenarios.generate import leaks_hidden  # noqa: E402


def load(path, cls):
    return [cls.model_validate_json(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


def main() -> int:
    bank = load_bank()
    personas = {p.id: p for p in load("data/personas/personas.jsonl", DoctorPersona)}
    rows = load("data/scenarios/scenarios.jsonl", Scenario)
    errs: list[str] = []
    if len(rows) < 36:
        errs.append(f"场景数 {len(rows)} < 36")
    missing = {s.id for s in bank.scene_skeletons} - {r.skeleton_id for r in rows}
    if missing:
        errs.append(f"缺少骨架：{sorted(missing)}")
    for r in rows:
        p = personas.get(r.persona_id)
        sk = next((s for s in bank.scene_skeletons if s.id == r.skeleton_id), None)
        if p is None or sk is None:
            errs.append(f"{r.id} 画像或骨架不存在")
            continue
        if leaks_hidden(p.hidden_objection, r.context_brief, r.pre_info, r.opening_line, r.rep_goal):
            errs.append(f"{r.id} 泄露隐藏异议")
        if re.search(r"\d+(\.\d+)?\s*%", r.context_brief + r.pre_info):
            errs.append(f"{r.id} 含百分比")
        if r.opening_line not in sk.opening_lines:
            errs.append(f"{r.id} 开场白不在骨架库中")
        if r.skeleton_id in ("S12", "S13") and (not r.baits or not r.hard_gate):
            errs.append(f"{r.id} 合规场景缺少 baits 或 hard_gate")
        if "主任" not in p.title and any("主任" in x for x in (r.rep_goal, r.context_brief, r.pre_info, *r.success_criteria)):
            errs.append(f"{r.id} 称呼与职称不符")
    print(f"场景 {len(rows)} 个；覆盖骨架 {len({r.skeleton_id for r in rows})}/14；类型分布 "
          f"{ {t: sum(1 for r in rows if r.type == t) for t in sorted({r.type for r in rows})} }")
    if errs:
        print("校验失败：")
        print("\n".join(" - " + e for e in errs))
        return 1
    print("场景集校验通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
