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
    client = TestClient(app)
    assert client.post("/api/auth/register", json={"username": "repone", "password": "correct-horse-123"}).status_code == 200
    yield client, DEMO[1]
    app.dependency_overrides.clear()


def test_full_flow(ctx):
    c, _persona = ctx
    r = c.post("/api/sessions", json={"scenario_id": "scn_001", "rep_id": "rep_1"})
    assert r.status_code == 200
    sid = r.json()["session_id"]
    assert r.json()["opening_line"] == "我只有几分钟，你说吧。"
    assert len(c.get("/api/sessions").json()) == 1

    t = c.post(f"/api/sessions/{sid}/turns", json={"text": "  张主任您好  "})
    assert t.status_code == 200 and t.json()["doctor_reply"] == "嗯，继续说。" and t.json()["ended"] is False
    assert t.json()["signals"] == ["relevant_to_concern"]

    g = c.get(f"/api/sessions/{sid}")
    assert [x["speaker"] for x in g.json()["turns"]] == ["doctor", "rep", "doctor"]
    assert g.json()["turns"][1]["text"] == "张主任您好"

    f = c.post(f"/api/sessions/{sid}/finish")
    assert f.json() == {"session_id": sid, "ended": True, "end_reason": "rep_ended", "report_id": f"report_{sid}"}
    report = c.get(f"/api/reports/report_{sid}")
    assert report.status_code == 200 and report.json()["scoring_mode"] == "unavailable"
    assert report.json()["turns"][1]["text"] == "张主任您好"
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
        for secret in (persona.hidden_objection, '"hidden_objection":', '"traps":', '"meta":', '"bait":'):
            assert secret not in t


def test_natural_end_creates_one_report(ctx):
    c, _ = ctx
    sid = c.post("/api/sessions", json={"scenario_id": "scn_001"}).json()["session_id"]
    for _ in range(12):
        response = c.post(f"/api/sessions/{sid}/turns", json={"text": "请您谈谈关注点。"})
        assert response.status_code == 200
        if response.json()["ended"]:
            assert response.json()["report_id"] == f"report_{sid}"
            break
    else:
        pytest.fail("会话未按轮数自然结束")
    assert c.get(f"/api/reports/report_{sid}").status_code == 200
    assert c.post(f"/api/sessions/{sid}/finish").json()["report_id"] == f"report_{sid}"


def test_other_account_cannot_read_or_change_session(ctx):
    c, _ = ctx
    sid = c.post("/api/sessions", json={"scenario_id": "scn_001", "rep_id": "forged"}).json()["session_id"]
    assert c.get(f"/api/sessions/{sid}").json()["rep_id"].startswith("usr_")
    other = TestClient(app)
    assert other.get("/api/sessions").status_code == 401
    assert other.post("/api/auth/register", json={"username": "reptwo", "password": "correct-horse-456"}).status_code == 200
    assert other.get("/api/sessions").json() == []
    assert other.get(f"/api/sessions/{sid}").status_code == 404
    assert other.post(f"/api/sessions/{sid}/turns", json={"text": "你好"}).status_code == 404
    assert other.post(f"/api/sessions/{sid}/finish").status_code == 404
    c.post(f"/api/sessions/{sid}/finish")
    assert other.get(f"/api/reports/report_{sid}").status_code == 404
