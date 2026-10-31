from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from ..diary_rehearsal import rehearsal_mood, triggered_wording
from ..llm import LLMProvider, load_prompt, structured_call
from ..models import DoctorPersona, DoctorState, RadarPracticeCue, Scenario, Session, Turn
from ..models.constants import SIGNALS
from ..personas.generate import DEPT_CN
from ..personas.validate import CONCERN_KEYWORDS
from ..scenarios.generate import leaks_hidden
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
}
REACTION = {
    "relevant_to_concern": "愿意继续听下去", "asked_open_question": "愿意多讲一点自己的情况",
    "cited_evidence": "点头，但会追问细节或适用人群", "empathy_shown": "语气略放松",
    "addressed_objection": "认可其回应，但仍保留一点怀疑", "vague_or_generic": "追问具体内容或出处",
    "pushy": "表示不舒服，收紧话题", "exaggeration": "对夸大表述表示不信任，追问依据",
    "off_label_claim": "指出这可能超出说明书适应症，质疑其合规", "competitor_bashing": "对贬低竞品明显反感",
    "ignored_doctor_question": "重复你的问题并要求直接回答", "proposed_next_step": "按你当前的信任度决定是否接受，不要轻易答应",
}
BAIT_DIRECTIVE = {
    "off_label_bait": "这一轮请自然地试探：问代表这个药能不能用于脂肪肝或其他尚未确认的适应症或人群（用你自己的话，不要点破你在测试）。",
    "competitor_bash_bait": "这一轮请抛出一个竞品话题，引导代表评价或比较竞品（看他是否会贬低对方）。",
    "exaggeration_bait": "这一轮请问一个绝对化的问题，例如能不能保证有效、是不是比其他药都好，引诱代表夸大。",
}
END_DIRECTIVE = {
    "doctor_left": "你已失去耐心，请礼貌但明确地结束这次对话（例如表示还有门诊、今天先到这里）。",
    "time_up": "时间到了，请简短收尾；态度保留，不要做出任何承诺。",
    "agreed_next_step": "你认可代表提出的下一步，请简短确认并约定后续。",
}
FALLBACK = {
    "rigorous_evidence": "这个数据的出处是哪里？把具体的研究名称和结论说清楚。",
    "busy_efficient": "我时间不多，你直接说重点。",
    "skeptical_challenger": "听起来和别的药差不多，你凭什么说它更好？",
    "friendly_open": "嗯，你接着说，我听着。",
    "conservative_habit": "我现在的方案挺稳定的，为什么要换？",
}
END_FALLBACK = {
    "doctor_left": "不好意思，我还有门诊，今天先到这里。",
    "time_up": "时间差不多了，资料先放这儿，我有需要再联系你。",
    "agreed_next_step": "好的，那就按你说的安排，我们下次再聊。",
}
_NUM = re.compile(r"\d+(?:\.\d+)?\s*%|\d+\.\d+")


def safe_text(s: str) -> str:
    """防止用户文本里的 {{...}} 被当作模板变量。"""
    return s.replace("{{", "{ {").replace("}}", "} }")


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
    judge_note: str = ""
    judge_degraded: bool = False


class SessionEngine:
    def __init__(self, provider: LLMProvider, kb=None, rules: StateRules | None = None):
        self.provider = provider
        self.kb = kb
        self.rules = rules or load_rules()

    # ---- 对外接口 ----
    def start(self, scenario: Scenario, persona: DoctorPersona, rep_id: str, session_id: str | None = None,
              diary_id: str | None = None, radar_id: str | None = None,
              radar_searched_at: datetime | None = None,
              radar_cues: list[RadarPracticeCue] | None = None) -> Session:
        state = initial_state(persona)
        return Session(
            id=session_id or f"sess_{uuid.uuid4().hex[:10]}", scenario_id=scenario.id, rep_id=rep_id,
            diary_id=diary_id, radar_id=radar_id, radar_searched_at=radar_searched_at,
            radar_cues=radar_cues or [],
            started_at=datetime.now(UTC),
            turns=[Turn(idx=0, speaker="doctor", text=scenario.opening_line, state_after=state,
                        meta={"rep_turn_no": 0})])

    def step(self, session: Session, scenario: Scenario, persona: DoctorPersona, rep_text: str,
             rehearsal_note: str = "") -> StepResult:
        rep_text = rep_text.strip()
        rep_turn_no = sum(t.speaker == "rep" for t in session.turns) + 1
        prev_state = next((t.state_after for t in reversed(session.turns) if t.state_after), initial_state(persona))
        history = format_history(session.turns)
        facts = self._retrieve(rep_text, persona) if scenario.program_id == "xinermei" else []

        indication_facts = self._indication_facts() if scenario.program_id == "xinermei" else []
        signals, judge_note, j_deg = self._judge(scenario, persona, history, rep_text, facts + indication_facts)
        state = apply_signals(prev_state, signals, self.rules, natural_decay(persona))
        end = decide_end(state, signals, rep_turn_no, persona.time_budget_turns, self.rules)
        reveal = end is None and should_reveal(state, signals, self.rules)
        if reveal:
            state.revealed_hidden_objection = True
        metas = [t.meta for t in session.turns if t.speaker == "doctor"]
        bait = None if (reveal or end) else next_bait(persona, metas, rep_turn_no, self.rules)
        wording = triggered_wording(rehearsal_note, rep_text) if not (reveal or bait or end) else ""
        mood = rehearsal_mood(rehearsal_note)
        cue_already_used = any(turn.meta.get("radar_cue_used") for turn in session.turns if turn.speaker == "doctor")
        radar_cue = session.radar_cues[0] if session.radar_cues and not cue_already_used else None

        reply, r_deg = self._reply(scenario, persona, state, signals, history, rep_text, facts, reveal, bait, end,
                                  rehearsal_note, wording, mood, radar_cue)

        session.turns.append(Turn(idx=len(session.turns), speaker="rep", text=rep_text, signals=signals,
                                  state_after=state, meta={"judge_note": judge_note, "judge_degraded": j_deg}))
        session.turns.append(Turn(idx=len(session.turns), speaker="doctor", text=reply, state_after=state,
                                  meta={"rep_turn_no": rep_turn_no, "bait": bait, "revealed": reveal,
                                        "end_hint": end, "degraded": j_deg or r_deg,
                                        "diary_wording_triggered": bool(wording),
                                        "diary_mood": mood or "", "radar_cue_used": bool(radar_cue and not
                                                                                           (reveal or bait or end or wording))}))
        if end:
            session.ended_at = datetime.now(UTC)
            session.end_reason = end
        return StepResult(reply, state, signals, end is not None, end, j_deg or r_deg, judge_note, j_deg)

    # ---- 内部 ----
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

    def _judge(self, scenario, persona, history, rep_text, facts) -> tuple[list[str], str, bool]:
        if self.provider.name == "mock" and not self.provider.responses:
            return self._demo_signals(rep_text), "", True
        user = load_prompt("signal_judge").render(
            scenario_type=scenario.type, concerns="、".join(CONCERN_CN[c] for c in persona.concerns),
            style=persona.style, hidden_objection=persona.hidden_objection, facts=format_facts(facts),
            history=history, rep_text=safe_text(rep_text))
        try:
            out, degraded = structured_call(
                self.provider, prompt_name="signal_judge", system="你是严格输出 JSON 的裁判。",
                messages=[{"role": "user", "content": user}], model_cls=JudgeOut, fallback=JudgeOut(),
                max_retries=1, temperature=0.2, max_tokens=256)
        except RuntimeError as exc:
            log.warning("信号判断暂不可用，使用备用规则：%s", exc)
            return self._demo_signals(rep_text), "", True
        note = out.note.strip()[:30] if not degraded else ""
        if note and leaks_hidden(persona.hidden_objection, note):
            note = ""
        return [s for s in dict.fromkeys(out.signals) if s in SIGNALS][:6], note, degraded

    @staticmethod
    def _demo_signals(rep_text: str) -> list[str]:
        """离线演示只识别明确的沟通行为，不判断医学内容真伪。"""
        signals = []
        if any(x in rep_text for x in ("如何", "怎样", "为什么", "哪些", "怎么看", "什么顾虑")):
            signals.append("asked_open_question")
        if any(x in rep_text for x in ("理解您", "理解你的", "理解您的顾虑", "您担心")):
            signals.append("empathy_shown")
        if any(x in rep_text for x in ("下次交流", "约个时间", "再约", "提供资料", "发给您资料")):
            signals.append("proposed_next_step")
        if any(x in rep_text for x in ("根治", "无副作用", "保证有效", "绝对有效")):
            signals.append("exaggeration")
        if any(x in rep_text for x in ("必须用", "马上用", "现在就用")):
            signals.append("pushy")
        return signals

    def _directive(self, reveal: bool, bait: str | None, end: str | None) -> str:
        if end:
            return END_DIRECTIVE[end]
        parts = []
        if reveal:
            parts.append("这一轮请自然地流露你真实的顾虑（用你自己的话，不要照搬原句，可以只透露一部分）。")
        if bait:
            parts.append(BAIT_DIRECTIVE[bait])
        return " ".join(parts) or "按人设自然回应。"

    def _fallback(self, persona: DoctorPersona, end: str | None) -> str:
        return END_FALLBACK[end] if end else FALLBACK[persona.style]

    def _check_reply(self, persona, reply, reveal, corpus) -> str | None:
        if not reveal and leaks_hidden(persona.hidden_objection, reply):
            return "直接说出了隐藏的顾虑"
        if unsupported_numbers(reply, corpus):
            return "出现了资料和对话中不存在的数字"
        return None

    def _reply(self, scenario, persona, state, signals, history, rep_text, facts, reveal, bait, end,
               rehearsal_note: str = "", wording: str = "", mood: str | None = None,
               radar_cue: RadarPracticeCue | None = None) -> tuple[str, bool]:
        academic_active = radar_cue is not None and not (reveal or bait or end or wording)
        fallback = (f"‘{wording}’这说法我不太喜欢，换个角度讲。" if wording else
                    self._fallback(persona, end) if end else
                    "这条公开资料的出处和适用范围，你能说清吗？" if academic_active else
                    "我只有几分钟，你先说重点。" if mood == "rushed" else
                    "你先说重点，别绕。" if mood == "irritable" else self._fallback(persona, None))
        if self.provider.name == "mock" and not self.provider.responses:
            if end:
                return fallback, True
            if wording:
                return fallback, True
            if "exaggeration" in signals:
                return "这个说法有依据吗？我们还是按说明书和公开研究讨论。", True
            if "pushy" in signals:
                return "请不要替我做决定，先把资料说明白。", True
            if "asked_open_question" in signals:
                return "我更关心适用人群和安全性，您能先说明资料出处吗？", True
            if "proposed_next_step" in signals:
                return "先把资料留下，我看完再决定要不要继续交流。", True
            return fallback, True
        prompt = load_prompt("doctor_reply")
        corpus = rep_text + format_facts(facts) + history
        sig_cn = "；".join(SIGNAL_CN[s] for s in signals) or "无明显信号，按人设自然回应"
        reaction = "；".join(REACTION[s] for s in signals) or "按人设自然回应"
        setting_cn = "，".join(str(scenario.setting[k]) for k in ("where", "duration", "state")
                              if scenario.setting.get(k)) or "门诊间隙"
        intent_cn = "结束拜访" if end else "回应代表并追问一个重点"
        if reveal:
            intent_cn = "流露真实顾虑"
        elif bait:
            intent_cn = "提出一个需要判断的问题"
        elif wording:
            intent_cn = "指出代表这轮重复使用的表达方式"
        elif academic_active:
            intent_cn = "就一条公开学术候选资料追问证据出处"
        elif mood == "irritable":
            intent_cn = "简短催促代表，并追问一个重点"
        elif mood == "rushed":
            intent_cn = "提醒时间很紧，并追问一个重点"
        directive = (f"代表这轮再次用了‘{wording}’。按主观日记中的沟通观察，"
                     "你可以对这个说法提出异议并请他换个角度讲；不要声称这是现实医生的真实偏好。"
                     if wording else self._directive(reveal, bait, end))
        if mood and not (reveal or bait or end or wording):
            directive = ("先用一句短促的话催代表讲重点，再只追问一个具体问题。"
                         if mood == "irritable" else "先表示时间很紧、请代表直说重点，再只追问一个具体问题。")
        if academic_active:
            directive = (f"你在这场虚构练习的背景资料里看到一条题为《{safe_text(radar_cue.topic)}》的公开网页候选。"
                         "请追问代表这类资料的出处、适用范围或证据局限；不要声称你或任何特定医生发表、参加了这项内容，"
                         "也不要把标题里的医学说法当成已核实结论。")
        note = ""
        for _ in range(2):
            user = prompt.render(
                department_cn=DEPT_CN[persona.department], title=persona.title, hospital_tier=persona.hospital_tier,
                style_desc=STYLE_DESC[persona.style], concerns="、".join(CONCERN_CN[c] for c in persona.concerns),
                current_habit=persona.current_habit, backstory=persona.backstory,
                speech_habits=persona.speech_habits, hidden_objection=persona.hidden_objection,
                tone_hint=(tone_hint(state) + ("；这场虚构练习可表现出不耐烦，回答更短，必要时打断空泛表达" if mood == "irritable"
                                              else "；这场虚构练习时间紧，说话更短，催代表先讲重点" if mood == "rushed"
                                              else "")),
                signals_cn=sig_cn, reaction_hint=reaction, facts=format_facts(facts),
                history=history, rep_text=safe_text(rep_text), directive=self._directive(reveal, bait, end),
                setting_cn=setting_cn, intent_cn=intent_cn,
                intent_directive=directive,
                examples=self._fallback(persona, end),
                rehearsal_note=safe_text(rehearsal_note) if rehearsal_note else "（无）",
                academic_context=(f"公开网页候选题材：《{safe_text(radar_cue.topic)}》；仅供这场虚构练习提出证据问题。"
                                  if academic_active else "（无）"),
                retry_note=note)
            try:
                out, degraded = structured_call(
                    self.provider, prompt_name="doctor_reply", system="你是严格输出 JSON 的角色扮演助手。",
                    messages=[{"role": "user", "content": user}], model_cls=DoctorReply,
                    fallback=DoctorReply(reply=fallback), max_retries=1,
                    temperature=0.8, max_tokens=256)
            except RuntimeError as exc:
                log.warning("医生回复暂不可用，使用备用台词：%s", exc)
                return fallback, True
            if degraded:
                return out.reply, True
            reason = self._check_reply(persona, out.reply, reveal, corpus)
            if academic_active and re.search(r"(?:我|本人|我们科).{0,10}(?:发表|参加|演讲|主持|写了|做了这项研究)", out.reply):
                reason = "把同名候选学术活动说成了自己的经历"
            if reason is None:
                return out.reply, False
            note = f"【上一次不合格：{reason}。请重写并避免该问题。】"
        return fallback, True
