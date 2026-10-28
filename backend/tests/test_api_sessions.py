import json

import pytest
from app.db import Repo
from app.deps import get_engine, get_repo
from app.llm import MockLLM
from app.main import app
from app.personas import build_demo_personas
from app.sessions import SessionEngine, StateRules
from fastapi.testclient import TestClient

from tests.factories import make_scenario

DEMO = build_demo_personas()


@pytest.fixture()
def ctx(tmp_path):
    repo = Repo(f"sqlite:///{tmp_path}/s.db")
    for p in DEMO:
        repo.save(p)
    repo.save(make_scenario(id="scn_001", persona_id=DEMO[1].id, opening_line="我只有几分钟，你说吧。"))
    mock = MockLLM({"signal_judge": json.dumps({"signals": ["relevant_to_concern"], "note": ""}),
                    "doctor_reply": json.dumps({"reply": "嗯，继续说。"}, ensure_ascii=False)})
    engine = SessionEngine(mock, kb=None, rules=StateRules())
    app.dependency_overrides[get_repo] = lambda: repo
    app.dependency_overrides[get_engine] = lambda: engine
    yield TestClient(app), DEMO[1]
    app.dependency_overrides.clear()


def test_full_flow(ctx):
    c, persona = ctx  # noqa: RUF059
    r = c.post("/api/sessions", json={"scenario_id": "scn_001", "rep_id": "rep_1"})
    assert r.status_code == 200
    sid = r.json()["session_id"]
    assert r.json()["opening_line"] == "我只有几分钟，你说吧。"

    t = c.post(f"/api/sessions/{sid}/turns", json={"text": "  张主任您好  "})
    assert t.status_code == 200 and t.json()["doctor_reply"] == "嗯，继续说。" and t.json()["ended"] is False
    assert t.json()["signals"] == ["relevant_to_concern"]

    g = c.get(f"/api/sessions/{sid}")
    assert [x["speaker"] for x in g.json()["turns"]] == ["doctor", "rep", "doctor"]
    assert g.json()["turns"][1]["text"] == "张主任您好"

    f = c.post(f"/api/sessions/{sid}/finish")
    assert f.json() == {"session_id": sid, "ended": True, "end_reason": "rep_ended", "report_id": None}
    assert c.post(f"/api/sessions/{sid}/turns", json={"text": "还有吗"}).status_code == 409


def test_validation_and_404(ctx):
    c, _ = ctx
    assert c.post("/api/sessions", json={"scenario_id": "nope", "rep_id": "r"}).status_code == 404
    sid = c.post("/api/sessions", json={"scenario_id": "scn_001", "rep_id": "r"}).json()["session_id"]
    assert c.post(f"/api/sessions/{sid}/turns", json={"text": "   "}).status_code == 422
    assert c.post(f"/api/sessions/{sid}/turns", json={"text": "x" * 2001}).status_code == 422
    assert c.get("/api/sessions/none").status_code == 404
    assert c.post("/api/sessions/none/turns", json={"text": "hi"}).status_code == 404


def test_no_secrets_in_any_response(ctx):
    c, persona = ctx
    sid = c.post("/api/sessions", json={"scenario_id": "scn_001", "rep_id": "r"}).json()["session_id"]
    texts = [c.post(f"/api/sessions/{sid}/turns", json={"text": "您好"}).text, c.get(f"/api/sessions/{sid}").text]
    for t in texts:
        for secret in (persona.hidden_objection, "hidden_objection", "traps", "meta", "bait"):
            assert secret not in t


def test_pre_goal_and_visit_note_flow(ctx):
    c, _ = ctx
    sid = c.post("/api/sessions", json={"scenario_id": "scn_001", "rep_id": "r", "pre_goal": "让医生约下次沟通"}).json()["session_id"]
    assert c.get(f"/api/sessions/{sid}").json()["pre_goal"] == "让医生约下次沟通"
    assert c.post(f"/api/sessions/{sid}/record", json={"note": "客户原话：先放资料。下一步：下周回访。"}).status_code == 409
    c.post(f"/api/sessions/{sid}/finish")
    assert c.post(f"/api/sessions/{sid}/record", json={"note": "客户原话：先放资料。下一步：下周回访。"}).json()["saved"] is True
    assert c.post(f"/api/sessions/{sid}/record", json={"note": "太短"}).status_code == 422
    assert "下周回访" in c.get(f"/api/sessions/{sid}").json()["visit_note"]
