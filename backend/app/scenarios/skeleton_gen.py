"""骨架场景生成器：骨架由人定（scene_bank_v1.yaml），模型只补两段背景文字。
任何一步失败都有确定性兜底，所以一定能产出完整场景集。"""
from __future__ import annotations

import logging
import re
from collections import Counter
from pathlib import Path

from pydantic import BaseModel, Field

from ..corpus.loader import SceneBank, Skeleton
from ..corpus.maps import SKELETON_BAITS, SKELETON_TYPE
from ..llm import BudgetExceeded, LLMProvider, load_prompt, structured_call
from ..models import DoctorPersona, Scenario
from ..personas.generate import DEPT_CN
from .generate import TRAP_WORDS, leaks_hidden

log = logging.getLogger(__name__)
E, C, H = "endocrinology", "cardiology", "hepatology"
PLAN: dict[str, list[str]] = {   # 每个骨架生成哪些科室的变体，合计 36 个
    "S01": [E, C, H], "S02": [E, C, H], "S03": [E, C, H], "S04": [E, C, H], "S05": [E, C, H],
    "S06": [E, C], "S07": [E, C, H], "S08": [E, C, H], "S09": [E, C], "S10": [E, C], "S11": [E, C],
    "S12": [E, C, H], "S13": [H, E], "S14": [E, C],
}
DIFF_BY_TRUST = {"low": {"hard"}, "mid": {"normal"}, "low_to_mid": {"normal", "hard"}}
_PCT = re.compile(r"\d+(?:\.\d+)?\s*%")


class FillDraft(BaseModel):
    context_brief: str = Field(min_length=20, max_length=160)
    pre_info: str = Field(min_length=10, max_length=120)


def pick_persona(personas: list[DoctorPersona], sk: Skeleton, dept: str, used: Counter) -> DoctorPersona:
    pool = [p for p in personas if p.department == dept] or list(personas)
    styles = set(sk.doctor.get("style_options", []))
    diffs = DIFF_BY_TRUST.get(sk.doctor.get("start_trust"), set())

    def score(p: DoctorPersona) -> int:
        return (3 if p.style in styles else 0) + (2 if p.difficulty in diffs else 0) - used[p.id] * 2

    best = sorted(pool, key=lambda p: (-score(p), p.id))[0]  # noqa: FURB192
    used[best.id] += 1
    return best


def honorific(p: DoctorPersona) -> str:
    """称呼要与职称一致：主任医师、副主任医师可称主任，主治医师只能称医生。"""
    return "主任" if "主任" in p.title else "医生"


def localize(text: str, p: DoctorPersona) -> str:
    h = honorific(p)
    return text if h == "主任" else text.replace("主任", h)


def check_fill(p: DoctorPersona, d: FillDraft) -> str | None:
    text = d.context_brief + d.pre_info
    if honorific(p) != "主任" and "主任" in text:
        return "称呼与职称不符（主治医师不应称主任）"
    if leaks_hidden(p.hidden_objection, d.context_brief, d.pre_info):
        return "泄露了医生的隐藏异议"
    if any(w in text for w in TRAP_WORDS):
        return "出现了陷阱类字眼"
    if _PCT.search(text):
        return "包含百分比数据"
    return None


def fallback_fill(sk: Skeleton, p: DoctorPersona) -> FillDraft:
    pre = localize(sk.rep_pre_info, p)
    brief = f"您将拜访{DEPT_CN[p.department]}的{p.title}（{p.hospital_tier}）。{pre}"
    return FillDraft(context_brief=brief[:160], pre_info=pre[:120])


def _setting_cn(setting: dict) -> str:
    return "，".join(str(setting[k]) for k in ("where", "duration", "state") if setting.get(k)) or "门诊间隙"


def fill_one(provider: LLMProvider | None, sk: Skeleton, p: DoctorPersona,
             max_attempts: int = 2) -> tuple[FillDraft, str]:
    """返回 (草稿, 来源)；来源为 "llm" 或 "fallback"。"""
    if provider is None:
        return fallback_fill(sk, p), "fallback"
    prompt = load_prompt("scenario_fill")
    retry = ""
    for _ in range(max_attempts):
        user = prompt.render(
            skeleton_title=sk.title, rep_goal=localize(sk.rep_goal, p), rep_pre_info=localize(sk.rep_pre_info, p),
            setting=_setting_cn(sk.setting), department_cn=DEPT_CN[p.department], title=p.title,
            hospital_tier=p.hospital_tier, style=p.style, hidden_objection=p.hidden_objection, retry_note=retry)
        draft, degraded = structured_call(
            provider, prompt_name="scenario_fill", system="你是严格输出 JSON 的数据生成助手。",
            messages=[{"role": "user", "content": user}], model_cls=FillDraft,
            fallback=FillDraft.model_construct(), max_retries=1, temperature=0.7)
        if degraded:
            retry = "【上一次输出无法解析，请严格按 JSON 格式输出。】"
            continue
        why = check_fill(p, draft)
        if why is None:
            return draft, "llm"
        retry = f"【上一次不合格：{why}。请重写并避免该问题。】"
    return fallback_fill(sk, p), "fallback"


def build_scenarios(provider: LLMProvider | None, personas: list[DoctorPersona], bank: SceneBank,
                    out_dir: str | Path = "data/scenarios") -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    used: Counter = Counter()
    seen_sk: Counter = Counter()
    scenarios: list[Scenario] = []
    via: Counter = Counter()
    budget_exceeded = False
    for sk in bank.scene_skeletons:
        for dept in PLAN.get(sk.id, []):
            p = pick_persona(personas, sk, dept, used)
            try:
                draft, how = fill_one(None if budget_exceeded else provider, sk, p)
            except BudgetExceeded:
                budget_exceeded = True
                draft, how = fallback_fill(sk, p), "fallback"
            via[how] += 1
            opening = sk.opening_lines[seen_sk[sk.id] % len(sk.opening_lines)]
            seen_sk[sk.id] += 1
            scenarios.append(Scenario(
                id=f"scn_{len(scenarios) + 1:03d}", type=SKELETON_TYPE[sk.id], persona_id=p.id,
                rep_goal=localize(sk.rep_goal, p), context_brief=draft.context_brief, opening_line=opening,
                success_criteria=[localize(c, p) for c in sk.success_criteria], source="generated", skeleton_id=sk.id,
                setting=dict(sk.setting), pre_info=draft.pre_info, turn_plan=list(sk.turn_plan),
                gold_moves=list(sk.gold_moves), compliance_checks=list(sk.compliance_checks),
                baits=list(SKELETON_BAITS.get(sk.id, [])), events=list(sk.events),
                hard_gate=sk.hard_gate, post_task=sk.post_task))
    (out / "scenarios.jsonl").write_text("\n".join(s.model_dump_json() for s in scenarios) + "\n", encoding="utf-8")
    dept_of = {p.id: p.department for p in personas}
    return {
        "personas": len(personas), "scenarios": len(scenarios), "via": dict(via),
        "budget_exceeded": budget_exceeded,
        "matrix": dict(Counter(f"{dept_of[s.persona_id]}/{s.skeleton_id}" for s in scenarios)),
        "types": dict(Counter(s.type for s in scenarios)),
    }
