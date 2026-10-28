import pytest
from app.models import DoctorState
from app.personas import build_demo_personas
from app.sessions.rules import StateRules, load_rules
from app.sessions.state import (
    apply_signals,
    decide_end,
    initial_state,
    natural_decay,
    next_bait,
    should_reveal,
)
from pydantic import ValidationError

DEMO = build_demo_personas()
R = StateRules()


def test_default_rules_file_loads_and_matches_defaults():
    assert load_rules("data/rubric/state_rules.yaml").deltas == R.deltas


def test_rules_reject_unknown_signal():
    with pytest.raises(ValidationError):
        StateRules(deltas={"nope": {"trust": 1}})


def test_apply_signals_math_and_clamp():
    s = DoctorState(trust=50, patience=50, engagement=50)
    out = apply_signals(s, ["asked_open_question", "empathy_shown", "asked_open_question"], R, decay=7)
    assert (out.trust, out.engagement, out.patience) == (59, 56, 43)    # 重复信号只计一次
    low = apply_signals(DoctorState(trust=5, patience=5, engagement=5), ["off_label_claim"], R, decay=3)
    assert (low.trust, low.patience) == (0, 0)


def test_natural_decay_leaves_margin_for_time_up():
    p = DEMO[2]   # hard, patience 35, 5 回合
    assert natural_decay(p) == pytest.approx(35 / 6)


def test_reveal_requires_open_question_and_trust():
    hi, lo = DoctorState(trust=60), DoctorState(trust=50)
    assert should_reveal(hi, ["asked_open_question"], R)
    assert not should_reveal(lo, ["asked_open_question"], R)
    assert not should_reveal(hi, ["empathy_shown"], R)
    assert not should_reveal(DoctorState(trust=60, revealed_hidden_objection=True), ["asked_open_question"], R)


def test_decide_end_priority():
    assert decide_end(DoctorState(trust=90, patience=0), ["proposed_next_step"], 9, 3, R) == "doctor_left"
    assert decide_end(DoctorState(trust=90, patience=40), ["proposed_next_step"], 3, 3, R) == "agreed_next_step"
    assert decide_end(DoctorState(trust=90, patience=40), ["proposed_next_step", "exaggeration"], 3, 3, R) == "time_up"
    assert decide_end(DoctorState(trust=50, patience=40), [], 2, 3, R) is None


def test_next_bait_timing_and_spacing():
    B = ["off_label_bait", "competitor_bash_bait"]
    assert next_bait(B, [], 1, R) is None
    assert next_bait(B, [], 2, R) == "off_label_bait"
    fired = [{"bait": "off_label_bait", "rep_turn_no": 2}]
    assert next_bait(B, fired, 3, R) is None                     # 间隔不足
    assert next_bait(B, fired, 4, R) == "competitor_bash_bait"
    both = fired + [{"bait": "competitor_bash_bait", "rep_turn_no": 4}]
    assert next_bait(B, both, 9, R) is None
    assert next_bait([], [], 5, R) is None                 # 无陷阱


def test_initial_state_by_difficulty():
    assert initial_state(DEMO[0]).engagement == 60 and initial_state(DEMO[2]).engagement == 40
