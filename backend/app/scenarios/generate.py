from __future__ import annotations

import json
import logging
import re
from collections import Counter
from pathlib import Path

from pydantic import BaseModel, Field

from ..llm import BudgetExceeded, LLMProvider, load_prompt, structured_call
from ..models import DoctorPersona, Scenario
from ..personas.validate import _grams

log = logging.getLogger(__name__)

TYPE_DESC = {
    "first_visit": "代表首次拜访该医生，双方不熟悉，目标是建立初步认知并争取下一次沟通机会",
    "post_conference": "代表在学术会议后跟进，医生对会上内容有印象但有疑问",
    "safety_concern": "医生对药品安全性（如胃肠道反应）有明确顾虑，代表需先共情再用证据回应",
    "competitor_compare": "医生已有熟悉的竞品用药习惯，会要求代表说明与竞品的差异",
    "time_pressure": "医生时间极少，会打断并要求直奔重点",
    "revisit_after_rejection": "上次拜访被医生明确拒绝或冷处理，本次需要换角度重新建立沟通",
    "off_label_bait": "医生会在交流中试探性询问未获批适应症或超说明书用法，考察代表是否守住合规边界；背景中不要点明此点",
}
TYPE_PLAN = {
    "endocrinology": ["first_visit", "competitor_compare", "safety_concern", "post_conference",
                      "time_pressure", "revisit_after_rejection"],
    "cardiology": ["first_visit", "post_conference", "safety_concern", "time_pressure", "competitor_compare"],
    "hepatology": ["off_label_bait", "first_visit", "off_label_bait", "safety_concern", "off_label_bait",
                   "post_conference", "off_label_bait", "first_visit", "off_label_bait", "safety_concern"],
}
TYPE_QUERY = {
    "first_visit": "产品 机制 适应症 体重管理 2型糖尿病",
    "post_conference": "研究 结果 头对头 学术",
    "safety_concern": "胃肠道 不良反应 安全性",
    "competitor_compare": "司美格鲁肽 头对头 对比",
    "time_pressure": "核心 优势 适应症",
    "revisit_after_rejection": "价格 医保 竞品 顾虑",
    "off_label_bait": "脂肪肝 在研 适应症 未获批",
}
_PUNCT = re.compile(r"[\s，。,.、；;：:！!？?（）()“”\"'‘’\-—]+")
TRAP_WORDS = ["诱导", "陷阱", "隐藏", "暗中", "考察合规", "试探"]


class ScenarioDraft(BaseModel):
    rep_goal: str = Field(min_length=6, max_length=120)
    context_brief: str = Field(min_length=20, max_length=220)
    opening_line: str = Field(min_length=4, max_length=60)
    success_criteria: list[str] = Field(min_length=2, max_length=5)


def _norm(s: str) -> str:
    return _PUNCT.sub("", s)


def leaks_hidden(hidden: str, *texts: str, window: int = 6, jaccard: float = 0.45) -> bool:
    h = _norm(hidden)
    for t in texts:
        n = _norm(t)
        if any(h[i:i + window] in n for i in range(max(1, len(h) - window + 1))):
            return True
        gh, gn = _grams(h), _grams(n)
        if gh and gn and len(gh & gn) / len(gh | gn) >= jaccard:
            return True
    return False


def check_draft(p: DoctorPersona, d: ScenarioDraft) -> str | None:
    """返回不合格原因；None 表示通过。"""
    if leaks_hidden(p.hidden_objection, d.context_brief, d.opening_line, d.rep_goal):
        return "泄露了医生的隐藏异议"
    if any(w in d.context_brief for w in TRAP_WORDS):
        return "context_brief 出现陷阱类字眼"
    if re.search(r"\d+(\.\d+)?\s*%", d.context_brief + d.opening_line):
        return "包含百分比数据"
    return None


def assign_types(personas: list[DoctorPersona]) -> list[tuple[DoctorPersona, str]]:
    """按科室的类型计划，为每位画像贪心分配一个场景类型（确定性）。"""
    out: list[tuple[DoctorPersona, str]] = []
    for dept, plan in TYPE_PLAN.items():
        pool = sorted([p for p in personas if p.department == dept], key=lambda p: p.id)
        for i in range(len(pool)):
            t = plan[i % len(plan)]

            def score(p: DoctorPersona, t=t):
                s = 0
                if t == "off_label_bait" and "off_label_bait" in p.traps:
                    s += 10
                if t != "off_label_bait" and "off_label_bait" in p.traps:
                    s -= 1   # 保护带 off_label_bait 陷阱的画像，优先留给 off_label_bait 槽位
                if t == "competitor_compare" and "competitor_comparison" in p.concerns:
                    s += 5
                if t == "time_pressure" and p.time_budget_turns <= 5:
                    s += 5
                if t == "safety_concern" and "safety_gi" in p.concerns:
                    s += 5
                if t == "revisit_after_rejection" and p.difficulty == "hard":
                    s += 3
                if t == "first_visit" and p.difficulty != "hard":
                    s += 1
                return s

            best = max(pool, key=score)       # 同分取最前（pool 已按 id 排序）
            pool.remove(best)
            out.append((best, t))
            # 重新排列后续索引保持：用 i 递增，pool 缩小
    return out


def facts_digest(kb, scenario_type: str) -> str:
    if kb is None:
        return "（无）"
    try:
        chunks = kb.retrieve(TYPE_QUERY[scenario_type], k=4)
    except Exception as e:  # noqa: BLE001
        log.warning("检索失败：%s", e)
        return "（无）"
    return "\n".join(f"- [{'已核验' if c.verified else '未核验'}] {c.text[:120]}" for c in chunks) or "（无）"


def generate_one(provider: LLMProvider, persona: DoctorPersona, scenario_type: str, kb=None,
                 max_attempts: int = 3) -> tuple[ScenarioDraft | None, str | None]:
    prompt = load_prompt("scenario_gen")
    persona_json = persona.model_dump_json(indent=2, exclude={"id"})
    retry_note = ""
    last_reason: str | None = "未生成"
    for _ in range(max_attempts):
        user = prompt.render(type=scenario_type, type_desc=TYPE_DESC[scenario_type], persona_json=persona_json,
                             facts_digest=facts_digest(kb, scenario_type), retry_note=retry_note)
        draft, degraded = structured_call(
            provider, prompt_name="scenario_gen", system="你是严格输出 JSON 的数据生成助手。",
            messages=[{"role": "user", "content": user}], model_cls=ScenarioDraft,
            fallback=ScenarioDraft.model_construct(), max_retries=1, temperature=0.8)
        if degraded:
            last_reason = "模型输出无法解析"
            continue
        reason = check_draft(persona, draft)
        if reason is None:
            return draft, None
        last_reason = reason
        retry_note = f"【上一次不合格：{reason}。请重写并避免该问题。】"
    return None, last_reason


def run_scenarios(provider: LLMProvider, personas: list[DoctorPersona], kb=None,
                  out_dir: str | Path = "data/scenarios") -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    scenarios: list[Scenario] = []
    rejects: list[dict] = []
    budget_exceeded = False
    for n, (p, t) in enumerate(assign_types(personas), start=1):
        try:
            draft, reason = generate_one(provider, p, t, kb)
        except BudgetExceeded:
            budget_exceeded = True
            break
        if draft is None:
            rejects.append({"persona_id": p.id, "type": t, "reason": reason})
            continue
        scenarios.append(Scenario(id=f"scn_{len(scenarios) + 1:03d}", type=t, persona_id=p.id,
                                  source="generated", **draft.model_dump()))
    (out / "scenarios.jsonl").write_text("\n".join(s.model_dump_json() for s in scenarios) + ("\n" if scenarios else ""),
                                         encoding="utf-8")
    (out / "rejects.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rejects) + ("\n" if rejects else ""), encoding="utf-8")
    dept_of = {p.id: p.department for p in personas}
    return {
        "personas": len(personas), "scenarios": len(scenarios), "rejected": len(rejects),
        "budget_exceeded": budget_exceeded,
        "matrix": dict(Counter(f"{dept_of[s.persona_id]}/{s.type}" for s in scenarios)),
        "reject_reasons": dict(Counter(r["reason"] for r in rejects)),
    }


def write_scenario_report(report: dict, path: str | Path = "docs/SCENARIO_REPORT.md") -> None:
    lines = ["# 场景生成报告", ""] + [f"- {k}: {v}" for k, v in report.items() if not isinstance(v, dict)]
    for k, v in report.items():
        if isinstance(v, dict):
            lines += ["", f"## {k}", ""] + ([f"- {a}: {b}" for a, b in sorted(v.items())] or ["- 无"])
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
