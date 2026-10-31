import json
from time import time

import pytest
from app.db import Repo
from app.deps import get_engine, get_repo
from app.llm import MockLLM
from app.main import app
from app.models.auth import Account
from app.personas import build_demo_personas
from app.sessions import SessionEngine, StateRules
from fastapi.testclient import TestClient
from sqlmodel import Session as DBSession

from tests.factories import make_scenario


@pytest.fixture()
def trial(tmp_path):
    repo = Repo(f"sqlite:///{tmp_path}/guest.db")
    persona = build_demo_personas()[1].model_copy(update={"time_budget_turns": 12, "initial_patience": 90})
    repo.save(persona)
    repo.save(make_scenario(id="scn_guest", persona_id=persona.id, opening_line="我只有几分钟，你说吧。"))
    provider = MockLLM({"signal_judge": json.dumps({"signals": [], "note": "表达清晰"}, ensure_ascii=False),
                        "doctor_reply": json.dumps({"reply": "请继续说。"}, ensure_ascii=False)})
    app.dependency_overrides[get_repo] = lambda: repo
    app.dependency_overrides[get_engine] = lambda: SessionEngine(provider, kb=None, rules=StateRules())
    yield TestClient(app), repo
    app.dependency_overrides.clear()


def test_guest_can_practice_privately_then_upgrade_without_losing_session(trial):
    client, repo = trial
    guest = client.post("/api/auth/guest")
    assert guest.status_code == 200 and guest.json()["is_guest"] is True
    assert "max-age=86400" in guest.headers["set-cookie"].lower()
    assert "httponly" in guest.headers["set-cookie"].lower()
    assert client.get("/api/auth/check").status_code == 204
    assert client.post("/api/auth/guest").json()["id"] == guest.json()["id"]
    assert len(client.get("/api/scenarios").json()) == 1

    created = client.post("/api/sessions", json={"scenario_id": "scn_guest"})
    assert created.status_code == 200
    sid = created.json()["session_id"]
    old_cookie = client.cookies.get("rep_trainer_session")
    turn = client.post(f"/api/sessions/{sid}/turns", json={"text": "您好，请说说您最关心的问题。"})
    assert turn.status_code == 200 and turn.json()["judge_note"] == "表达清晰"
    assert client.get(f"/api/sessions/{sid}").json()["rep_id"] == guest.json()["id"]

    other = TestClient(app)
    assert other.post("/api/auth/guest").status_code == 200
    assert other.get(f"/api/sessions/{sid}").status_code == 404
    assert other.get("/api/sessions").json() == []

    for private_path in ("/api/diary", "/api/radar"):
        assert client.get(private_path).status_code == 403
    for retired_path in ("/api/team", "/api/playbook-cards"):
        assert client.get(retired_path).status_code == 404
    assert client.post("/api/sessions", json={"scenario_id": "scn_guest", "diary_id": "diary_any"}).status_code == 403

    upgraded = client.post("/api/auth/upgrade", json={"username": "guestgraduate", "password": "strong-password-123"})
    assert upgraded.status_code == 200
    assert upgraded.json() == {"id": guest.json()["id"], "username": "guestgraduate", "is_guest": False}
    assert client.get(f"/api/sessions/{sid}").status_code == 200
    assert client.get("/api/diary").status_code == 200
    stale = TestClient(app)
    stale.cookies.set("rep_trainer_session", old_cookie)
    assert stale.get("/api/auth/me").status_code == 401
    assert client.post("/api/auth/logout").status_code == 200
    assert client.post("/api/auth/login", json={"username": "guestgraduate", "password": "strong-password-123"}).status_code == 200
    assert client.get(f"/api/sessions/{sid}").status_code == 200
    with DBSession(repo.engine) as db:
        saved = db.get(Account, guest.json()["id"])
        assert saved and saved.password_hash.startswith("pbkdf2_sha256$")


def test_guest_trial_limits_and_expiry(trial):
    client, repo = trial
    guest = client.post("/api/auth/guest").json()
    assert client.post("/api/auth/login", json={"username": guest["username"], "password": "random-password"}).status_code == 401
    sid = client.post("/api/sessions", json={"scenario_id": "scn_guest"}).json()["session_id"]
    for i in range(6):
        assert client.post(f"/api/sessions/{sid}/turns", json={"text": f"第 {i} 句，请继续。"}).status_code == 200
    assert client.post(f"/api/sessions/{sid}/turns", json={"text": "再说一句"}).status_code == 429
    assert client.post("/api/sessions", json={"scenario_id": "scn_guest"}).status_code == 200
    assert client.post("/api/sessions", json={"scenario_id": "scn_guest"}).status_code == 429

    with DBSession(repo.engine) as db:
        saved = db.get(Account, guest["id"])
        assert saved
        saved.created_at = int(time()) - 24 * 3600 - 1
        db.add(saved)
        db.commit()
    assert client.get("/api/auth/me").status_code == 401
