"""导出人工抽检清单 docs/REVIEW_SAMPLE.md。
有 prescreen.json：取风险最高的 14 个 + 随机 6 个低风险（用于校准你的判断）；否则按科室分层随机 20 个。"""
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, "backend")
from app.models import DoctorPersona, Scenario  # noqa: E402
from app.scenarios.review import PRESCREEN_PATH, load_review, rejected_ids  # noqa: E402


def load(path, cls):
    p = Path(path)
    return [cls.model_validate_json(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def main() -> int:
    personas = {p.id: p for p in load("data/personas/personas.jsonl", DoctorPersona)}
    bad = rejected_ids(load_review())
    scenarios = [s for s in load("data/scenarios/scenarios.jsonl", Scenario) if s.id not in bad]
    if not scenarios:
        print("没有场景可导出。")
        return 2
    rnd = random.Random(7)
    pre = json.loads(PRESCREEN_PATH.read_text(encoding="utf-8")) if PRESCREEN_PATH.exists() else {}
    if pre:
        ranked = sorted(scenarios, key=lambda s: -pre.get(s.id, {}).get("risk", 0))
        picked = ranked[:14]
        rest = [s for s in ranked[14:]]
        picked += rnd.sample(rest, min(6, len(rest)))
    else:
        by_dept = defaultdict(list)
        for s in scenarios:
            by_dept[personas[s.persona_id].department].append(s)
        picked = []
        for lst in by_dept.values():
            picked += rnd.sample(lst, min(max(1, 20 // len(by_dept)), len(lst)))
        rest = [s for s in scenarios if s not in picked]
        picked += rnd.sample(rest, min(20 - len(picked), len(rest)))

    lines = ["# 人工抽检清单", "",
             "请逐条阅读并在每条末尾**只勾选一项**（把 `[ ]` 改成 `[x]`），完成后运行 `python scripts/apply_review.py`。",
             "重点看：医生是否太配合？隐藏异议是否泄露？开场是否符合风格？背景是否出现编造数据？", ""]
    for i, s in enumerate(picked, 1):
        p = personas[s.persona_id]
        pr = pre.get(s.id)
        lines += [
            f"## {i}. {s.id}｜{s.type}｜{p.department}｜{p.difficulty}｜{p.style}", "",
            f"- 预筛：风险 {pr['risk']}，标记 {pr['flags']}，{pr['note']}" if pr else "- 预筛：无",
            f"- 画像：{p.title}／{p.hospital_tier}；关注点 {p.concerns}；陷阱 {p.traps}",
            f"- 现有习惯：{p.current_habit}", f"- **隐藏异议（代表看不到）**：{p.hidden_objection}",
            f"- 背景：{p.backstory}｜口头习惯：{p.speech_habits}", "",
            f"- 代表目标：{s.rep_goal}", f"- 给代表的背景：{s.context_brief}", f"- 医生开场：{s.opening_line}",
            f"- 达成标准：{s.success_criteria}", "",
            "- [ ] 通过　[ ] 需修改　[ ] 剔除　　备注：", "",
        ]
    Path("docs").mkdir(exist_ok=True)
    Path("docs/REVIEW_SAMPLE.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"已导出 {len(picked)} 个样本 -> docs/REVIEW_SAMPLE.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
