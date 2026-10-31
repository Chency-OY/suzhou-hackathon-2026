import json
from datetime import UTC, datetime

import httpx
from app.llm import MockLLM
from app.models import DoctorState, Scenario, Session, Turn
from app.scoring import score_session

from tests.factories import make_scenario


def _session(text: str = "您好，请问您最关注哪些治疗问题？") -> Session:
    return Session(id="sess_test", scenario_id="scn_test", rep_id="usr_test",
                   started_at=datetime.now(UTC), ended_at=datetime.now(UTC), end_reason="rep_ended",
                   turns=[Turn(idx=0, speaker="doctor", text="我只有几分钟。", state_after=DoctorState()),
                          Turn(idx=1, speaker="rep", text=text, state_after=DoctorState())])


def _scenario() -> Scenario:
    return make_scenario(id="scn_test", rep_goal="了解医生关注点")


def _draft(text: str, flags: list[dict] | None = None) -> str:
    return json.dumps({"dimension_scores": {"opening": 12, "discovery": 19, "product_evidence": 25,
                                              "objection_handling": 19, "closing": 9, "communication": 15},
                       "findings": [{"turn_idx": 1, "kind": "strength", "dimension": "discovery",
                                     "quote": text[:8], "explanation": "开放式探询"},
                                    {"turn_idx": 1, "kind": "issue", "dimension": "opening",
                                     "quote": "原文中不存在", "explanation": "编造定位"}],
                       "compliance_flags": flags or [], "summary": "沟通训练反馈",
                       "next_practice_tips": ["下一次追问顾虑"]}, ensure_ascii=False)


def test_scoring_clamps_dimensions_and_rejects_invented_quotes():
    session = _session()
    mock = MockLLM({"scorer": _draft(session.turns[1].text)})
    report = score_session(session, _scenario(), mock)
    assert report.scoring_mode == "model" and report.total_score == 97
    assert report.dimension_scores["opening"] == 10
    assert len(report.findings) == 1 and report.findings[0].quote in session.turns[1].text
    assert not report.capped_by_compliance


def test_redline_requires_rule_hit_and_model_confirmation():
    text = "我保证有效，您可以直接用。"
    session = _session(text)
    flag = {"rule_id": "C05", "turn_idx": 1, "quote": "保证有效"}
    mock = MockLLM({"scorer": _draft(text, [flag])})
    report = score_session(session, _scenario(), mock)
    assert report.capped_by_compliance and report.raw_total == 97 and report.total_score == 60
    assert any(f.kind == "compliance_violation" and f.quote == "保证有效" for f in report.findings)
    mock.set("scorer", _draft(text, [{**flag, "quote": "模型编造的引用"}]))
    assert not score_session(session, _scenario(), mock).capped_by_compliance
    mock.set("scorer", _draft("您好，请问", [flag]))
    assert not score_session(_session(), _scenario(), mock).capped_by_compliance


def test_no_model_response_keeps_report_without_numeric_score():
    report = score_session(_session(), _scenario(), MockLLM())
    assert report.scoring_mode == "unavailable" and report.total_score == 0
    assert "未生成数值评分" in report.review_note


def test_denied_claim_cannot_become_redline_even_if_model_flags_it():
    text = "不能保证有效，具体情况应查正式资料。"
    flag = {"rule_id": "C05", "turn_idx": 1, "quote": "保证有效"}
    report = score_session(_session(text), _scenario(), MockLLM({"scorer": _draft(text, [flag])}))
    assert not report.capped_by_compliance


def test_model_network_failure_keeps_report_available():
    def fail(_messages):
        raise httpx.ConnectError("offline")

    report = score_session(_session(), _scenario(), MockLLM({"scorer": fail}))
    assert report.scoring_mode == "unavailable" and report.findings == []
