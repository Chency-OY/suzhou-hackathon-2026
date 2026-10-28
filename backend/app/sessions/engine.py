from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from ..corpus.loader import SceneBank, load_bank
from ..llm import LLMProvider, load_prompt, structured_call
from ..models import DoctorPersona, DoctorState, Scenario, Session, Turn
from ..models.constants import SIGNALS
from ..personas.generate import DEPT_CN
from ..personas.validate import CONCERN_KEYWORDS
from ..scenarios.generate import leaks_hidden
from .intent import INTENTS, choose_intent, fallback_line, pick_examples, resolve_end
from .rules import StateRules, load_rules
from .state import apply_signals, decide_end, initial_state, natural_decay, next_bait, should_reveal

log = logging.getLogger(__name__)

STYLE_DESC = {
    "rigorous_evidence": "严谨循证型：重视数据与文献出处，常追问研究名称和适用人群",
    "busy_efficient": "忙碌效率型：时间极少，要求直奔重点，容易打断",
    "skeptical_challenger": "怀疑挑战型：爱质疑、爱对比，不轻易被说服",
    "friendly_open": "友好开放型：愿意交流，但仍会提出专业问题",
    "conservative_habit": "保守惯性型：习惯既有方案，对换药持保留态度",
}
CONCERN_CN = {
    "efficacy": "疗效", "safety_gi": "胃肠道安全性", "price_access": "价格与医保",
    "long_term_evidence": "长期证据", "patient_adherence": "患者依从性",
    "competitor_comparison": "与竞品对比", "cv_benefit": "心血管获益",
}
SIGNAL_CN = {
    "relevant_to_concern": "回应紧扣你的关注点", "asked_open_question": "代表问了开放式问题",
    "cited_evidence": "代表引用了具体证据", "empathy_shown": "代表理解了你的顾虑",
    "addressed_objection": "代表正面回应了你的疑问", "vague_or_generic": "代表的话空泛套话",
    "pushy": "代表在催促施压", "exaggeration": "代表的说法夸大或绝对化",
    "off_label_claim": "代表的说法可能超出说明书适应症", "competitor_bashing": "代表在贬低竞品",
    "ignored_doctor_question": "代表回避了你的提问", "proposed_next_step": "代表提出了具体下一步",
    "accepted_benefit": "代表接了利益试探", "disclosed_stat": "代表涉及处方量",
    "promised_outcome": "代表承诺了销售结果",
}
BAD_WORDS = ("信号", "评分", "系统", "训练", "设定", "意图")
_NUM = re.compile(r"\d+(?:\.\d+)?\s*%|\d+\.\d+")


def safe_text(s: str) -> str:
    """防止用户文本里的 {{...}} 被当作模板变量。"""
    return s.replace("{{", "{ {").replace("}}", "} }")


def setting_cn(setting: dict) -> str:
    return "，".join(str(setting[k]) for k in ("where", "duration", "state") if setting.get(k)) or "门诊间隙"


def format_history(turns: list[Turn], n: int = 8) -> str:
    return "\n".join(("代表" if t.speaker == "rep" else "医生") + "：" + safe_text(t.text) for t in turns[-n:]) or "（无）"


def format_facts(chunks) -> str:
    return "\n".join(f"- [{'已核验' if c.verified else '未核验'}] {c.text[:140]}" for c in chunks) or "（无）"


def tone_hint(s: DoctorState) -> str:
    parts = ["态度冷淡、简短、带质疑" if s.trust < 30 else "态度谨慎，会追问细节" if s.trust < 60
             else "相对放松，愿意多聊一点"]
    if s.patience < 25:
        parts.append("明显不耐烦，可以打断或催促")
    elif s.patience < 50:
        parts.append("有些着急")
    return "；".join(parts)


def unsupported_numbers(reply: str, corpus: str) -> list[str]:
    corp = re.sub(r"\s+", "", corpus)
    return [t for t in (re.sub(r"\s+", "", m) for m in _NUM.findall(reply)) if t not in corp]


class JudgeOut(BaseModel):
    signals: list[str] = Field(default_factory=list)
    note: str = ""


class DoctorReply(BaseModel):
    reply: str = Field(min_length=2, max_length=300)


@dataclass
class StepResult:
    doctor_reply: str
    state: DoctorState
    signals: list[str]
    ended: bool
    end_reason: str | None
    degraded: bool


class SessionEngine:
    def __init__(self, provider: LLMProvider, kb=None, rules: StateRules | None = None, bank: SceneBank | None = None):
        self.provider = provider
        self.kb = kb
        self.rules = rules or load_rules()
        self.bank = bank or load_bank()

    # ---- 对外接口 ----
    def start(self, scenario: Scenario, persona: DoctorPersona, rep_id: str, session_id: str | None = None) -> Session:
        state = initial_state(persona)
        return Session(
            id=session_id or f"sess_{uuid.uuid4().hex[:10]}", scenario_id=scenario.id, rep_id=rep_id,
            started_at=datetime.now(timezone.utc),  # noqa: UP017
            turns=[Turn(idx=0, speaker="doctor", text=scenario.opening_line, state_after=state,
                        meta={"rep_turn_no": 0})])

    def step(self, session, scenario, persona, rep_text) -> StepResult:
        rep_text = rep_text.strip()
        rep_turn_no = sum(t.speaker == "rep" for t in session.turns) + 1
        prev_state = next((t.state_after for t in reversed(session.turns) if t.state_after), initial_state(persona))
        history = format_history(session.turns)
        facts = self._retrieve(rep_text, persona)

        signals, j_deg = self._judge(scenario, persona, history, rep_text, facts + self._indication_facts())
        state = apply_signals(prev_state, signals, self.rules, natural_decay(persona))
        end = resolve_end(decide_end(state, signals, rep_turn_no, persona.time_budget_turns, self.rules),
                          state, scenario.skeleton_id)
        reveal = end is None and should_reveal(state, signals, self.rules)
        if reveal:
            state.revealed_hidden_objection = True
        metas = [t.meta for t in session.turns if t.speaker == "doctor"]
        baits = scenario.baits or [t for t in persona.traps if t != "none"]
        bait = None if (reveal or end) else next_bait(baits, metas, rep_turn_no, self.rules)
        last_intent = metas[-1].get("intent") if metas else None
        intent = choose_intent(end=end, bait=bait, reveal=reveal, signals=signals, state=state,
                               rep_turn_no=rep_turn_no, style=persona.style, last_intent=last_intent)
        event = self._event(scenario, rep_turn_no, end)
        reply, r_deg = self._reply(scenario, persona, state, history, rep_text, facts, intent,
                                   f"{session.id}:{rep_turn_no}")
        text = f"（{event}）{reply}" if event else reply

        session.turns.append(Turn(idx=len(session.turns), speaker="rep", text=rep_text, signals=signals,
                                  state_after=state))
        session.turns.append(Turn(idx=len(session.turns), speaker="doctor", text=text, state_after=state,
                                  meta={"rep_turn_no": rep_turn_no, "bait": bait, "revealed": reveal,
                                        "intent": intent, "event": event, "end_hint": end,
                                        "degraded": j_deg or r_deg}))
        if end:
            session.ended_at = datetime.now(timezone.utc)  # noqa: UP017
            session.end_reason = end
        return StepResult(text, state, signals, end is not None, end, j_deg or r_deg)

    # ---- 内部 ----
    def _event(self, scenario, rep_turn_no, end):
        if end or not scenario.events or rep_turn_no not in (2, 4):
            return None
        return scenario.events[(rep_turn_no // 2 - 1) % len(scenario.events)]

    def _retrieve(self, rep_text: str, persona: DoctorPersona) -> list:
        if self.kb is None:
            return []
        try:
            qs = [rep_text[:120], " ".join(k for c in persona.concerns[:2] for k in CONCERN_KEYWORDS.get(c, [])[:2])]
            seen, out = set(), []
            for q in qs:
                if q.strip():
                    for c in self.kb.retrieve(q, k=3):
                        if c.id not in seen:
                            seen.add(c.id)
                            out.append(c)
            return out[:5]
        except Exception as e:  # noqa: BLE001
            log.warning("检索失败：%s", e)
            return []

    def _indication_facts(self) -> list:
        if self.kb is None:
            return []
        try:
            return self.kb.retrieve("适应症 获批 说明书", k=2)
        except Exception:  # noqa: BLE001
            return []

    def _judge(self, scenario, persona, history, rep_text, facts) -> tuple[list[str], bool]:
        user = load_prompt("signal_judge").render(
            scenario_type=scenario.type, concerns="、".join(CONCERN_CN[c] for c in persona.concerns),
            style=persona.style, hidden_objection=persona.hidden_objection, facts=format_facts(facts),
            history=history, rep_text=safe_text(rep_text))
        out, degraded = structured_call(
            self.provider, prompt_name="signal_judge", system="你是严格输出 JSON 的裁判。",
            messages=[{"role": "user", "content": user}], model_cls=JudgeOut, fallback=JudgeOut(),
            max_retries=1, temperature=0.2)
        return [s for s in dict.fromkeys(out.signals) if s in SIGNALS][:6], degraded

    def _check_reply(self, persona, reply, intent, corpus) -> str | None:
        if len(reply.strip()) > 60:
            return "太长，医生一般只说一两句短话"
        if any(w in reply for w in BAD_WORDS):
            return "出现了不该出现的字眼"
        if intent != "reveal_case" and leaks_hidden(persona.hidden_objection, reply):
            return "直接说出了隐藏的顾虑"
        if unsupported_numbers(reply, corpus):
            return "出现了资料和对话中不存在的数字"
        return None

    def _reply(self, scenario, persona, state, history, rep_text, facts, intent, seed) -> tuple[str, bool]:
        prompt = load_prompt("doctor_reply")
        cn, directive, _, _ = INTENTS[intent]
        examples = "\n".join("- " + e for e in pick_examples(self.bank, intent, 3, seed))
        corpus = rep_text + format_facts(facts) + history
        note = ""
        for _ in range(2):
            user = prompt.render(
                department_cn=DEPT_CN[persona.department], title=persona.title, hospital_tier=persona.hospital_tier,
                style_desc=STYLE_DESC[persona.style], speech_habits=persona.speech_habits,
                current_habit=persona.current_habit, hidden_objection=persona.hidden_objection,
                setting_cn=setting_cn(scenario.setting), history=history, rep_text=safe_text(rep_text),
                intent_cn=cn, intent_directive=directive, tone_hint=tone_hint(state), examples=examples,
                facts=format_facts(facts), retry_note=note)
            out, degraded = structured_call(
                self.provider, prompt_name="doctor_reply", system="你是严格输出 JSON 的角色扮演助手。",
                messages=[{"role": "user", "content": user}], model_cls=DoctorReply,
                fallback=DoctorReply(reply=fallback_line(self.bank, intent, seed)), max_retries=1, temperature=0.8)
            if degraded:
                return out.reply, True
            reason = self._check_reply(persona, out.reply, intent, corpus)
            if reason is None:
                return out.reply.strip(), False
            note = f"【上一次不合格：{reason}。请重写并避免该问题。】"
        return fallback_line(self.bank, intent, seed), True
