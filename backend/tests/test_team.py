from datetime import UTC, datetime

import pytest
from app.db import Repo
from app.deps import get_repo
from app.main import app
from app.models import Report, Session, Turn
from fastapi.testclient import TestClient


@pytest.fixture()
def clients(tmp_path):
    repo = Repo(f"sqlite:///{tmp_path}/team.db")
    app.dependency_overrides[get_repo] = lambda: repo
    names = ("owner01", "member02", "outside03")
    clients = [TestClient(app) for _ in names]
    ids = []
    for index, (client, name) in enumerate(zip(clients, names), start=1):
        client.headers["x-real-ip"] = f"198.51.100.{index}"
        response = client.post("/api/auth/register", json={"username": name, "password": "test-password-123"})
        assert response.status_code == 200
        ids.append(response.json()["id"])
    yield repo, clients, ids
    app.dependency_overrides.clear()


def _save_session(repo: Repo, sid: str, owner_id: str, signals: list[str], score: int) -> None:
    repo.save(Session(id=sid, scenario_id="synthetic_scenario", rep_id=owner_id,
                      started_at=datetime.now(UTC), ended_at=datetime.now(UTC), end_reason="rep_ended",
                      turns=[Turn(idx=0, speaker="doctor", text="虚构问题"),
                             Turn(idx=1, speaker="rep", text="虚构回答", signals=signals)]))
    repo.save(Report(id=f"report_{sid}", session_id=sid, dimension_scores={}, total_score=score,
                     raw_total=score, scoring_mode="model"))


def test_team_aggregates_only_current_members_without_raw_dialogues(clients):
    repo, (owner, member, outsider), (owner_id, member_id, outsider_id) = clients
    assert outsider.get("/api/team/insights").status_code == 404
    created = owner.post("/api/team", json={"name": " 合成训练组 "})
    assert created.status_code == 200
    code = created.json()["invite_code"]
    assert len(code) >= 12 and created.json()["role"] == "owner"
    assert owner.get("/api/team").json()["invite_code"] == ""
    assert outsider.post("/api/team/join", json={"invite_code": "invalid-code-123"}).status_code == 404
    assert member.post("/api/team/join", json={"invite_code": code}).json()["member_count"] == 2
    assert member.post("/api/team/join", json={"invite_code": code}).status_code == 409
    assert member.post("/api/team/invite").status_code == 403
    new_code = owner.post("/api/team/invite").json()["invite_code"]
    assert new_code != code and owner.get("/api/team").json()["invite_code"] == ""
    assert outsider.post("/api/team/join", json={"invite_code": code}).status_code == 404
    assert owner.post("/api/team/leave").status_code == 409
    _save_session(repo, "s_owner", owner_id, ["pushy"], 42)
    _save_session(repo, "s_member", member_id, ["pushy", "asked_open_question"], 78)
    _save_session(repo, "s_outsider", outsider_id, ["exaggeration"], 1)
    result = member.get("/api/team/insights")
    assert result.status_code == 200
    body = result.json()
    assert body["completed_sessions"] == 2 and body["scored_sessions"] == 2
    assert body["average_score"] == 60 and body["signal_counts"]["pushy"] == 2
    assert body["signal_counts"]["exaggeration"] == 0
    assert "虚构回答" not in result.text and owner_id not in result.text and member_id not in result.text
    assert member.post("/api/team/leave").json() == {"ok": True}
    assert member.get("/api/team/insights").status_code == 404
    assert owner.get("/api/team/insights").json()["completed_sessions"] == 1
    assert outsider.post("/api/team", json={"name": "另一训练组"}).status_code == 200
    assert outsider.get("/api/team/insights").json()["completed_sessions"] == 1
