"""随机抽 20 个场景（按科室分层）导出为人工抽检清单 docs/REVIEW_SAMPLE.md。"""
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, "backend")
from app.models import DoctorPersona, Scenario  # noqa: E402


def load(path, cls):
    p = Path(path)
    return [cls.model_validate_json(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def main() -> int:
    personas = {p.id: p for p in load("data/personas/personas.jsonl", DoctorPersona)}
    scenarios = load("data/scenarios/scenarios.jsonl", Scenario)
    if not scenarios:
        print("没有场景可导出。")
        return 2
    rnd = random.Random(7)
    by_dept = defaultdict(list)
    for s in scenarios:
        by_dept[personas[s.persona_id].department].append(s)
    picked = []
    per = max(1, 20 // len(by_dept))
    for dept, lst in by_dept.items():
        picked += rnd.sample(lst, min(per, len(lst)))
    rest = [s for s in scenarios if s not in picked]
    picked += rnd.sample(rest, min(20 - len(picked), len(rest)))
    lines = ["# 人工抽检清单", "", "请逐条阅读并在每条末尾勾选。重点看：医生是否太配合？隐藏异议是否泄露？"
             "开场是否符合风格？背景是否出现编造数据？", ""]
    for i, s in enumerate(picked, 1):
        p = personas[s.persona_id]
        lines += [
            f"## {i}. {s.id}｜{s.type}｜{p.department}｜{p.difficulty}｜{p.style}", "",
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
