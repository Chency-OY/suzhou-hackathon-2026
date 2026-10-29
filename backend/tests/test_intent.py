import pytest
from app.corpus import load_bank
from app.models import DoctorState
from app.sessions.intent import INTENTS, choose_intent, fallback_line, pick_examples, resolve_end

BANK = load_bank()


def ci(**kw):
    base = dict(end=None, bait=None, reveal=False, signals=[], state=DoctorState(trust=50, patience=60, engagement=50),  # noqa: C408
                rep_turn_no=3, style="friendly_open", last_intent=None)
    base.update(kw)
    return choose_intent(**base)


def test_resolve_end():
    hi, lo = DoctorState(trust=70), DoctorState(trust=50)
    assert resolve_end("time_up", hi, None) == "materials_left"
    assert resolve_end("time_up", lo, None) == "soft_decline"
    assert resolve_end("time_up", hi, "S06") == "referred"
    assert resolve_end("time_up", hi, "S07") == "soft_decline"
    assert resolve_end("doctor_left", hi, "S06") == "doctor_left"
    assert resolve_end(None, hi, None) is None


def test_boundary_intents():
    assert ci(signals=["declined_boundary"]) == "accept_boundary"
    assert ci(signals=["evaded_boundary"]) == "press_again"
    assert ci(signals=["declined_boundary", "proposed_next_step"]) == "accept_boundary"
    assert ci(signals=["accepted_benefit", "declined_boundary"]) == "pull_back"
    assert ci(bait="stat_bait", signals=["evaded_boundary"]) == "bait_stat"


def test_avoid_recent_lines_and_variety():
    for intent in ("close_hard", "close_soft", "close_followup", "close_materials"):
        assert len(pick_examples(BANK, intent, 99, "s")) >= 3
    full = pick_examples(BANK, "close_hard", 99, "s")
    got = fallback_line(BANK, "close_hard", "s", avoid=[full[0], full[1]])
    assert got not in full[:2]
    assert fallback_line(BANK, "close_hard", "s", avoid=full) in full            # 全避开时退回完整池，不崩


def test_repeat_question_examples_name_the_question():
    for e in pick_examples(BANK, "repeat_question", 99, "s"):
        assert "这个" not in e and "那个" not in e


def test_closing_intents():
    assert ci(end="doctor_left") == "close_hard" and ci(end="agreed_next_step") == "close_followup"
    assert ci(end="materials_left") == "close_materials" and ci(end="referred") == "close_refer"
    assert ci(end="soft_decline") == "close_soft"


def test_priority_order():
    assert ci(bait="off_label_bait") == "bait_off_label"
    assert ci(bait="benefit_bait", signals=["exaggeration"]) == "bait_benefit"
    assert ci(reveal=True, signals=["pushy"]) == "reveal_case"
    assert ci(signals=["off_label_claim", "cited_evidence"]) == "push_back_label"
    assert ci(signals=["exaggeration"]) == "push_back_evidence"
    assert ci(signals=["competitor_bashing"]) == "push_back_tone"
    for s in ("accepted_benefit", "disclosed_stat", "promised_outcome"):
        assert ci(signals=[s]) == "pull_back"
    assert ci(signals=["pushy"]) == "cool_down"
    assert ci(signals=["ignored_doctor_question"]) == "repeat_question"
    assert ci(signals=["vague_or_generic"]) == "ask_specific"


def test_normal_flow():
    assert ci(style="busy_efficient", signals=["asked_open_question"]) == "time_pressure"
    assert ci(style="busy_efficient", signals=["proposed_next_step"]) == "hedge_next"     # 先回应对方提出的下一步
    assert ci(state=DoctorState(trust=50, patience=10), signals=["proposed_next_step"]) == "hedge_next"
    assert ci(style="busy_efficient", signals=["asked_open_question"], last_intent="time_pressure") == "open_up"
    assert ci(signals=[], rep_turn_no=1, state=DoctorState(trust=20, patience=60)) == "hard_refuse"
    assert ci(signals=[], rep_turn_no=1) == "soft_refuse"
    assert ci(signals=[], rep_turn_no=4) == "ask_specific"
    assert ci(signals=["cited_evidence"]) == "probe_evidence"
    assert ci(signals=["proposed_next_step", "relevant_to_concern"]) == "hedge_next"
    assert ci(signals=["asked_open_question"]) == "open_up"
    assert ci(state=DoctorState(trust=50, patience=20), signals=["asked_open_question"]) == "time_pressure"


@pytest.mark.parametrize("intent", sorted(INTENTS))
def test_every_intent_has_examples_and_short_lines(intent):
    cn, directive, _, _ = INTENTS[intent]
    assert cn and directive
    ex = pick_examples(BANK, intent, 3, seed="s1")
    assert ex and len(set(ex)) == len(ex)
    assert fallback_line(BANK, intent, "s1") in pick_examples(BANK, intent, 99, seed="s1")
    assert all("%" not in e for e in ex)


def test_examples_are_deterministic_and_use_bank():
    assert pick_examples(BANK, "soft_refuse", 3, "a") == pick_examples(BANK, "soft_refuse", 3, "a")
    assert all(x in BANK.lines("soft_refusal") for x in pick_examples(BANK, "soft_refuse", 3, "a"))
    pool = pick_examples(BANK, "close_followup", 99, "z")
    assert fallback_line(BANK, "close_followup", "z") in pool
    assert BANK.closing("followup_set")[0] in pool                      # 台词库里的句子仍在池中
