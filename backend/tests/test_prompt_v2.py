import re

from app.llm import load_prompt

DOCTOR_VARS = {"department_cn", "title", "hospital_tier", "style_desc", "speech_habits", "current_habit",
               "hidden_objection", "setting_cn", "history", "rep_text", "intent_cn", "intent_directive",
               "tone_hint", "examples", "facts", "rehearsal_note", "retry_note"}
FILL_VARS = {"skeleton_title", "rep_goal", "rep_pre_info", "setting", "department_cn", "title", "hospital_tier",
             "style", "hidden_objection", "retry_note"}


def vars_of(name: str) -> set[str]:
    return set(re.findall(r"\{\{(\w+)\}\}", load_prompt(name).body))


def test_doctor_reply_variables_and_version():
    assert load_prompt("doctor_reply").version.startswith("0.3")
    assert vars_of("doctor_reply") == DOCTOR_VARS


def test_scenario_fill_variables():
    assert vars_of("scenario_fill") == FILL_VARS


def test_judge_has_compliance_signals():
    body = load_prompt("signal_judge").body
    for s in ("accepted_benefit", "disclosed_stat", "promised_outcome", "declined_boundary"):
        assert s in body
