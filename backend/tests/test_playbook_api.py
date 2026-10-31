import json
from datetime import UTC, datetime

import pytest
from app.db import Repo
from app.deps import get_provider, get_repo
from app.llm import MockLLM
from app.main import app
from app.models import Report, Scenario, Session, Turn
from app.models.domain import PlaybookDraft
from app.personas import build_demo_personas
from app.playbook import card_is_safe
from fastapi.testclient import TestClient

from tests.factories import make_scenario


@pytest.fixture()
def setup(tmp_path):
    repo = Repo(f"sqlite:///{tmp_path}/cards.db")
    persona = build_demo_personas()[0]
    repo.save(persona)
    repo.save(make_scenario(id="scn_training", persona_id=persona.id))
    draft = {"title": "先问再回应", "situation": "对方表达保留态度，需要先澄清顾虑",
             "effective_response_pattern": "复述顾虑，提出开放式问题，再约定提供可核对资料",
             "example_lines": ["您最关注哪方面？", "我先核对资料，再与您讨论。"]}
    mock = MockLLM({"playbook_extract": json.dumps(draft, ensure_ascii=False)})
    app.dependency_overrides[get_repo] = lambda: repo
    app.dependency_overrides[get_provider] = lambda: mock
    owner, member, outside = [TestClient(app) for _ in range(3)]
    clients = (owner, member, outside)
    ids = []
    for index, (client, name) in enumerate(zip(clients, ("cardowner", "cardmember", "cardoutside")), start=20):
        client.headers["x-real-ip"] = f"198.51.100.{index}"
        response = client.post("/api/auth/register", json={"username": name, "password": "test-password-123"})
        assert response.status_code == 200
        ids.append(response.json()["id"])
    code = owner.post("/api/team", json={"name": "合成打法组"}).json()["invite_code"]
    assert member.post("/api/team/join", json={"invite_code": code}).status_code == 200
    assert outside.post("/api/team", json={"name": "另一训练组"}).status_code == 200
    repo.save(Session(id="sess_high", scenario_id="scn_training", rep_id=ids[1],
                      started_at=datetime.now(UTC), ended_at=datetime.now(UTC), end_reason="rep_ended",
                      turns=[Turn(idx=0, speaker="doctor", text="我比较谨慎。"),
                             Turn(idx=1, speaker="rep", text="您主要有哪些顾虑？我先核对资料。")]))
    repo.save(Report(id="report_sess_high", session_id="sess_high", dimension_scores={},
                     total_score=85, raw_total=85, scoring_mode="model"))
    yield repo, mock, owner, member, outside
    app.dependency_overrides.clear()


def test_card_requires_owner_review_and_team_scenario_is_private(setup):
    repo, mock, owner, member, outside = setup
    assert outside.post("/api/playbook-cards/extract", json={"session_id": "sess_high"}).status_code == 404
    result = member.post("/api/playbook-cards/extract", json={"session_id": "sess_high"})
    assert result.status_code == 200
    card = result.json()
    assert card["status"] == "candidate" and "evidence_session_ids" not in card
    assert "avg_score_of_source" not in card and "sess_high" not in result.text
    assert len(mock.calls) == 1
    assert member.post("/api/playbook-cards/extract", json={"session_id": "sess_high"}).json()["id"] == card["id"]
    assert len(mock.calls) == 1
    assert outside.get("/api/playbook-cards").json() == []
    assert member.post(f"/api/playbook-cards/{card['id']}/approve").status_code == 403
    approved = owner.post(f"/api/playbook-cards/{card['id']}/approve")
    assert approved.status_code == 200 and approved.json()["status"] == "approved"
    scenario_id = approved.json()["scenario_id"]
    assert repo.get(Report, "report_sess_high").total_score == 85
    assert outside.get(f"/api/scenarios/{scenario_id}").status_code == 404
    assert scenario_id not in [item["id"] for item in outside.get("/api/scenarios").json()]
    assert outside.post("/api/sessions", json={"scenario_id": scenario_id}).status_code == 404
    assert member.get(f"/api/scenarios/{scenario_id}").status_code == 200
    assert scenario_id in [item["id"] for item in member.get("/api/scenarios").json()]
    assert TestClient(app).get(f"/api/scenarios/{scenario_id}").status_code == 404
    assert member.post("/api/sessions", json={"scenario_id": scenario_id}).status_code == 200
    assert member.post("/api/team/leave").status_code == 200
    assert member.get(f"/api/scenarios/{scenario_id}").status_code == 200
    assert scenario_id not in [item["id"] for item in member.get("/api/scenarios").json()]
    assert member.post("/api/sessions", json={"scenario_id": scenario_id}).status_code == 404


def test_low_score_and_unsafe_model_output_are_rejected(setup):
    repo, mock, _, member, _ = setup
    report = repo.get(Report, "report_sess_high")
    report.total_score = 79
    repo.save(report)
    assert member.post("/api/playbook-cards/extract", json={"session_id": "sess_high"}).status_code == 422
    report.total_score = 85
    report.capped_by_compliance = True
    repo.save(report)
    assert member.post("/api/playbook-cards/extract", json={"session_id": "sess_high"}).status_code == 422
    report.capped_by_compliance = False
    repo.save(report)
    mock.set("playbook_extract", json.dumps({"title": "信尔美疗效好", "situation": "医生关心数据",
                                               "effective_response_pattern": "直接宣传疗效优越", "example_lines": []}, ensure_ascii=False))
    assert member.post("/api/playbook-cards/extract", json={"session_id": "sess_high"}).status_code == 503


def test_numbered_steps_are_cleaned_without_allowing_medical_numbers(setup):
    _, mock, _, member, _ = setup
    draft = {"title": "先问再回应", "situation": "对方有顾虑，先核实其真实关注点",
             "effective_response_pattern": "1. 复述顾虑；2. 追问需求；3. 约定资料核对",
             "example_lines": ["1. 您最关注哪方面？"]}
    mock.set("playbook_extract", json.dumps(draft, ensure_ascii=False))
    result = member.post("/api/playbook-cards/extract", json={"session_id": "sess_high"})
    assert result.status_code == 200
    assert "1." not in result.json()["effective_response_pattern"]
    assert "2." not in result.json()["effective_response_pattern"]
    assert "1." not in result.json()["example_lines"][0]
    assert not card_is_safe(PlaybookDraft(title="数字结论不安全", situation="对方要求提供证据说明",
                                          effective_response_pattern="直接引用12%的研究结论"))


def test_manager_can_reject_candidate_without_creating_scenario(setup):
    repo, _, owner, member, outside = setup
    card = member.post("/api/playbook-cards/extract", json={"session_id": "sess_high"}).json()
    assert member.post(f"/api/playbook-cards/{card['id']}/reject").status_code == 403
    rejected = owner.post(f"/api/playbook-cards/{card['id']}/reject")
    assert rejected.status_code == 200 and rejected.json()["status"] == "rejected"
    assert owner.post(f"/api/playbook-cards/{card['id']}/approve").status_code == 409
    assert repo.get(Report, "report_sess_high") is not None
    assert outside.get("/api/playbook-cards").json() == []
    assert repo.get(Scenario, f"scn_{card['id']}") is None
