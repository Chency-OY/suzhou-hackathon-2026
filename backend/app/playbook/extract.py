from __future__ import annotations

import logging
import re

import httpx

from ..llm import LLMProvider, load_prompt, structured_call
from ..models import DoctorPersona, PlaybookCard, Scenario, Session
from ..models.domain import PlaybookDraft

log = logging.getLogger(__name__)
_OBVIOUS_ID = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)|(?<!\d)\d{17}[\dXx](?!\w)|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
_NAME_SITE = re.compile(r"[\u4e00-\u9fff]{1,8}(?:医院|主任|教授)")
_DRUG = re.compile(r"信尔美|玛仕度肽|司美格鲁肽|替尔泊肽")
_NUMBER = re.compile(r"\d+(?:\.\d+)?%?")
_UNSAFE_CARD = re.compile(r"\d|[０-９]|@|https?://|医院|主任|教授|信尔美|玛仕度肽|司美格鲁肽|替尔泊肽|根治|无副作用|疗效|降糖|减重|优于|胜过")
_LIST_NUMBER = re.compile(r"(^|[；;])\s*[1-9][.、．)]\s*")


def _redact(text: str) -> str:
    text = _OBVIOUS_ID.sub("[身份信息]", text)
    text = _NAME_SITE.sub("[身份信息]", text)
    text = _DRUG.sub("[药品]", text)
    return _NUMBER.sub("[数字]", text)


def card_is_safe(card: PlaybookCard | PlaybookDraft) -> bool:
    items = [card.title, card.situation, card.effective_response_pattern, *card.example_lines]
    return all(item.strip() and len(item) <= 300 and not _UNSAFE_CARD.search(item) for item in items)


def _remove_list_numbers(text: str) -> str:
    return _LIST_NUMBER.sub(r"\1", text).strip()


def extract_card(session: Session, scenario: Scenario, persona: DoctorPersona,
                 provider: LLMProvider, card_id: str, team_id: str, owner_id: str,
                 score: int) -> PlaybookCard | None:
    if provider.name == "mock" and not provider.responses.get("playbook_extract"):
        return None
    transcript = "\n".join(f"{'代表' if turn.speaker == 'rep' else '模拟医生'}：{_redact(turn.text[:500])}"
                           for turn in session.turns[:20])
    prompt = load_prompt("playbook_extract").render(goal=_redact(scenario.rep_goal[:200]), transcript=transcript)
    try:
        draft, degraded = structured_call(
            provider, prompt_name="playbook_extract", system="你只输出安全、匿名的沟通打法 JSON。",
            messages=[{"role": "user", "content": prompt}], model_cls=PlaybookDraft,
            fallback=lambda: PlaybookDraft(title="无法提炼", situation="当前资料不足以安全提炼",
                                           effective_response_pattern="请重新选择合适的虚构演练"),
            max_retries=1, temperature=0.1, max_tokens=650)
    except (RuntimeError, httpx.HTTPError):
        log.warning("打法卡片整理模型暂不可用")
        return None
    draft = draft.model_copy(update={
        "title": _remove_list_numbers(draft.title),
        "situation": _remove_list_numbers(draft.situation),
        "effective_response_pattern": _remove_list_numbers(draft.effective_response_pattern),
        "example_lines": [_remove_list_numbers(item) for item in draft.example_lines],
    })
    if degraded or not card_is_safe(draft):
        return None
    return PlaybookCard(id=card_id, team_id=team_id, created_by=owner_id,
                        source_scenario_id=scenario.id, title=draft.title,
                        situation=draft.situation, effective_response_pattern=draft.effective_response_pattern,
                        example_lines=draft.example_lines[:3], applicable_scenario_types=[scenario.type],
                        applicable_departments=[persona.department], evidence_session_ids=[session.id],
                        avg_score_of_source=score, status="candidate")
