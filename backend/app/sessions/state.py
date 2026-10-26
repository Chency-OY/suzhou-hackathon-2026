from __future__ import annotations

from ..models import DoctorPersona, DoctorState
from .rules import StateRules

BASE_ENGAGEMENT = {"easy": 60, "normal": 50, "hard": 40}


def initial_state(p: DoctorPersona) -> DoctorState:
    return DoctorState(trust=p.initial_trust, patience=p.initial_patience, engagement=BASE_ENGAGEMENT[p.difficulty])


def natural_decay(p: DoctorPersona) -> float:
    """每个代表回合的自然耐心消耗。用 (回合上限+1) 做分母，保证正常对话在回合用尽时仍有余量，
    于是"时间到"先于"耐心耗尽"触发；只有负面信号才会让医生提前离开。"""
    return p.initial_patience / (p.time_budget_turns + 1)


def apply_signals(state: DoctorState, signals: list[str], rules: StateRules, decay: float) -> DoctorState:
    t, pa, e = state.trust, state.patience, state.engagement
    for s in dict.fromkeys(signals):
        d = rules.deltas.get(s, {})
        t += d.get("trust", 0)
        pa += d.get("patience", 0)
        e += d.get("engagement", 0)
    pa -= round(decay)
    return DoctorState(trust=t, patience=pa, engagement=e,
                       revealed_hidden_objection=state.revealed_hidden_objection)


def should_reveal(state_after: DoctorState, signals: list[str], rules: StateRules) -> bool:
    return (not state_after.revealed_hidden_objection and "asked_open_question" in signals
            and state_after.trust >= rules.reveal_min_trust)


def decide_end(state: DoctorState, signals: list[str], rep_turn_no: int, budget: int, rules: StateRules):
    """优先级：doctor_left > agreed_next_step > time_up。"""
    if state.patience <= 0:
        return "doctor_left"
    if (state.trust >= rules.agree_min_trust and "proposed_next_step" in signals
            and not (set(signals) & set(rules.negative_signals))):
        return "agreed_next_step"
    if rep_turn_no >= budget:
        return "time_up"
    return None


def next_bait(p: DoctorPersona, doctor_metas: list[dict], rep_turn_no: int, rules: StateRules) -> str | None:
    pending = [t for t in p.traps if t != "none"]
    fired = [m for m in doctor_metas if m.get("bait")]
    pending = [t for t in pending if t not in {m["bait"] for m in fired}]
    if not pending or rep_turn_no < rules.bait_min_rep_turns:
        return None
    if fired and rep_turn_no - max(m.get("rep_turn_no", 0) for m in fired) < rules.bait_spacing_rep_turns:
        return None
    return pending[0]
