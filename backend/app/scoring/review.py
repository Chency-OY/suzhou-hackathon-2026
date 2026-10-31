from __future__ import annotations

import logging
import re
from pathlib import Path

import httpx
import yaml

from ..llm import LLMProvider, load_prompt, structured_call
from ..models import Report, Scenario, Session
from ..models.constants import DIMENSION_WEIGHTS
from ..models.domain import Finding, ScorerDraft

log = logging.getLogger(__name__)
RULES_PATH = Path("data/rubric/compliance_rules.yaml")
_NEGATION = re.compile(r"不能|不可|不应|不会|并非|不是|无法|尚未获批|未获批|未经批准|不要")


def _candidates(session: Session) -> tuple[dict[tuple[str, int], str], int]:
    data = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))
    candidates: dict[tuple[str, int], str] = {}
    for rule in data["rules"]:
        pattern = rule.get("pattern")
        if rule.get("severity") != "red" or not pattern:
            continue
        for turn in session.turns:
            if turn.speaker == "rep" and (match := re.search(pattern, turn.text)):
                if _NEGATION.search(turn.text[max(0, match.start() - 10):match.end()]):
                    continue
                candidates[(rule["id"], turn.idx)] = match.group()
    return candidates, int(data["score_cap"])


def _unavailable(session: Session) -> Report:
    return Report(id=f"report_{session.id}", session_id=session.id,
                  dimension_scores={name: 0 for name in DIMENSION_WEIGHTS},
                  total_score=0, raw_total=0, capped_by_compliance=False, scoring_mode="unavailable",
                  summary="模型评分暂不可用，可继续逐句回看沟通信号。",
                  review_note="未生成数值评分；医学和合规内容仍需人工核对。")


def score_session(session: Session, scenario: Scenario, provider: LLMProvider) -> Report:
    if not session.ended_at or not any(turn.speaker == "rep" for turn in session.turns):
        return _unavailable(session)
    if provider.name == "mock" and not provider.responses.get("scorer"):
        return _unavailable(session)
    candidates, cap = _candidates(session)
    candidate_text = "\n".join(f"{rule_id} 第{idx}句：{quote}" for (rule_id, idx), quote in candidates.items()) or "无"
    transcript = "\n".join(f"[{turn.idx}] {'代表' if turn.speaker == 'rep' else '模拟医生'}：{turn.text[:700]}"
                           for turn in session.turns[:25])
    prompt = load_prompt("scorer").render(goal=scenario.rep_goal[:300],
                                          rule_candidates=candidate_text, transcript=transcript)
    try:
        draft, degraded = structured_call(
            provider, prompt_name="scorer", system="你只输出符合结构的 JSON 训练评分。",
            messages=[{"role": "user", "content": prompt}], model_cls=ScorerDraft,
            fallback=ScorerDraft(), max_retries=1, temperature=0.0, max_tokens=1600)
    except (RuntimeError, httpx.HTTPError):
        log.warning("训练评分模型暂不可用")
        return _unavailable(session)
    if degraded or not draft.dimension_scores:
        return _unavailable(session)
    scores = {name: min(max(int(draft.dimension_scores.get(name, 0)), 0), weight)
              for name, weight in DIMENSION_WEIGHTS.items()}
    rep_text = {turn.idx: turn.text for turn in session.turns if turn.speaker == "rep"}
    findings = [finding for finding in draft.findings
                if finding.dimension in DIMENSION_WEIGHTS and finding.turn_idx in rep_text
                and finding.quote in rep_text[finding.turn_idx]]
    confirmed = []
    for flag in draft.compliance_flags:
        candidate = candidates.get((flag.rule_id, flag.turn_idx))
        if (candidate and flag.turn_idx in rep_text and flag.quote in rep_text[flag.turn_idx]
                and candidate in flag.quote):
            confirmed.append(flag)
            findings.append(Finding(turn_idx=flag.turn_idx, kind="compliance_violation",
                                    dimension="communication", quote=flag.quote,
                                    explanation=f"命中待复核的合规规则 {flag.rule_id}；请交由带教或合规人员核对。"))
    raw = sum(scores.values())
    report = Report(id=f"report_{session.id}", session_id=session.id, dimension_scores=scores,
                    total_score=min(raw, cap) if confirmed else raw, raw_total=raw,
                    capped_by_compliance=bool(confirmed), findings=findings[:12],
                    summary=draft.summary or "已生成沟通训练参考评分。",
                    next_practice_tips=[tip[:240] for tip in draft.next_practice_tips[:3]],
                    scoring_mode="model",
                    review_note="仅供虚构演练参考；医学事实未自动核定，合规标记需人工复核。")
    return report
