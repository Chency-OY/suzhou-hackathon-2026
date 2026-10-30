from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from app.db import Repo
from app.deps import get_engine, get_repo
from app.diary_rehearsal import rehearsal_note
from app.llm import MockLLM
from app.main import app
from app.models.diary import DiaryDigest, FieldDiary
from app.personas import build_demo_personas
from app.sessions import SessionEngine, StateRules
from fastapi.testclient import TestClient

from tests.factories import make_scenario


def _diary(owner_id: str) -> FieldDiary:
    return FieldDiary(id="diary_test", owner_id=owner_id, created_at=datetime.now(UTC),
                      raw_text="今天我很紧张。医生说别用性价比。后来还说三代药疗效更好。",
                      digest=DiaryDigest(summary="拜访后回忆",
                                         first_impressions=["我很紧张"],
                                         doctor_feedback=["医生说别用性价比", "医生说三代药疗效更好"],
                                         uncertain_claims=["三代药疗效更好"]))


def test_only_communication_cues_enter_rehearsal_prompt():
    item = _diary("owner")
    note = rehearsal_note(item)
    assert "我很紧张" in note and "性价比" in note
    assert "三代药" not in note and "疗效" not in note
    persona = build_demo_personas()[1]
    scenario = make_scenario(persona_id=persona.id)
    mock = MockLLM({"signal_judge": json.dumps({"signals": []}),
                    "doctor_reply": json.dumps({"reply": "你先说重点。"}, ensure_ascii=False)})
    engine = SessionEngine(mock, kb=None, rules=StateRules())
    session = engine.start(scenario, persona, "owner", diary_id=item.id)
    engine.step(session, scenario, persona, "您好", rehearsal_note=note)
    prompt = next(call for call in mock.calls if call["prompt_name"] == "doctor_reply")["messages"][0]["content"]
    assert "主观回忆" in prompt and "性价比" in prompt and "三代药" not in prompt


def test_diary_rehearsal_is_account_scoped(tmp_path):
    repo = Repo(f"sqlite:///{tmp_path}/rehearsal.db")
    persona = build_demo_personas()[1]
    repo.save(persona)
    repo.save(make_scenario(id="scn_rehearsal", persona_id=persona.id))
    app.dependency_overrides[get_repo] = lambda: repo
    app.dependency_overrides[get_engine] = lambda: SessionEngine(MockLLM(), kb=None, rules=StateRules())
    first = TestClient(app, headers={"x-real-ip": str(uuid4())})
    second = TestClient(app, headers={"x-real-ip": str(uuid4())})
    try:
        assert first.post("/api/auth/register", json={"username": "noteone", "password": "long-password-123"}).status_code == 200
        assert second.post("/api/auth/register", json={"username": "notetwo", "password": "long-password-456"}).status_code == 200
        owner_id = first.get("/api/auth/me").json()["id"]
        repo.save(_diary(owner_id))
        body = {"scenario_id": "scn_rehearsal", "diary_id": "diary_test"}
        assert second.post("/api/sessions", json=body).status_code == 404
        created = first.post("/api/sessions", json=body)
        assert created.status_code == 200
        session_id = created.json()["session_id"]
        view = first.get(f"/api/sessions/{session_id}").json()
        assert view["diary_id"] == "diary_test" and "性价比" in view["rehearsal_note"]
        assert "三代药" not in view["rehearsal_note"]
        assert first.post(f"/api/sessions/{session_id}/turns", json={"text": "您好"}).status_code == 200
        repo.delete(FieldDiary, "diary_test")
        assert first.get(f"/api/sessions/{session_id}").json()["rehearsal_note"] == ""
    finally:
        app.dependency_overrides.clear()
