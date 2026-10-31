from __future__ import annotations

import json
from datetime import UTC, datetime

from app.llm import MockLLM
from app.models.diary import DiaryDigest, FieldDiary
from app.tribunal import assess_claim, candidate_facts, extract_claims


def test_claims_are_separate_from_communication_observations():
    diary = FieldDiary(id="d1", owner_id="u1", created_at=datetime.now(UTC), raw_text="原话保留。",
                       digest=DiaryDigest(summary="拜访后回忆", first_impressions=["我很紧张"],
                                          doctor_feedback=["医生说别提性价比", "医生说信尔美没有副作用"],
                                          uncertain_claims=["信尔美获批治疗脂肪肝"]))
    assert extract_claims(diary) == ["信尔美获批治疗脂肪肝", "医生说信尔美没有副作用"]
    assert candidate_facts("信尔美比三代药更好") == []
    safety = candidate_facts("信尔美没有副作用")
    assert safety and all(fact.category == "safety" for fact in safety)
    assert all(fact.source.startswith("label.md#") for fact in safety)
    assert candidate_facts("信尔美每周给药一次") == []  # 上游条目没有逐条定位到说明书章节


def test_verdict_needs_exact_quote_from_approved_source():
    fact = candidate_facts("信尔美没有副作用")[0]
    quote = "发生率 ≥2% 且高于安慰剂组的不良反应"
    assert quote in fact.statement
    mock = MockLLM({"diary_tribunal": json.dumps({"relation": "possible_conflict",
                                                   "evidence_id": fact.id, "evidence_quote": quote},
                                                  ensure_ascii=False)})
    finding = assess_claim("信尔美没有副作用", mock, [fact])
    assert finding.status == "possible_conflict"
    assert finding.evidence_quote == quote
    assert finding.candidates[0].url.startswith("https://img.innoventbio.com/")
    assert "医生姓名" not in mock.calls[0]["messages"][0]["content"]

    mock.set("diary_tribunal", json.dumps({"relation": "possible_conflict",
                                          "evidence_id": fact.id, "evidence_quote": "根本不存在的副作用结论"},
                                         ensure_ascii=False))
    invalid = assess_claim("信尔美没有副作用", mock, [fact])
    assert invalid.status == "insufficient" and invalid.evidence_quote == ""


def test_unrelated_claim_never_receives_a_drug_verdict():
    mock = MockLLM({"diary_tribunal": "{}"})
    finding = assess_claim("这位医生比较讨厌性价比", mock)
    assert finding.status == "out_of_scope" and mock.calls == []


def test_question_is_not_treated_as_an_assertion():
    mock = MockLLM({"diary_tribunal": "{}"})
    finding = assess_claim("医生问：信尔美有没有副作用？", mock)
    assert finding.status == "insufficient"
    assert finding.candidates
    assert mock.calls == []


def test_paraphrase_not_found_in_raw_words_cannot_get_a_verdict():
    mock = MockLLM({"diary_tribunal": "{}"})
    finding = assess_claim("信尔美没有副作用", mock, raw_text="主任问这个药有没有风险。")
    assert finding.status == "insufficient" and not finding.grounded_in_raw
    assert "原话" in finding.note
    assert mock.calls == []
