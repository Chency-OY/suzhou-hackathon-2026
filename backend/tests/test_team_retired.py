from datetime import UTC, datetime

from app.db import Repo
from app.deps import get_repo
from app.main import app
from app.models import Session
from fastapi.testclient import TestClient

from tests.factories import make_persona, make_scenario


def test_team_endpoints_are_retired_but_personal_history_remains(tmp_path):
    repo = Repo(f"sqlite:///{tmp_path}/retired-team.db")
    app.dependency_overrides[get_repo] = lambda: repo
    client = TestClient(app)
    other = TestClient(app)
    try:
        owner_id = client.post("/api/auth/register", json={"username": "oldmember",
                                                            "password": "long-password-123"}).json()["id"]
        other.post("/api/auth/register", json={"username": "othermember",
                                                "password": "long-password-123"})
        for path in ("/api/team", "/api/team/insights", "/api/playbook-cards"):
            assert client.get(path).status_code == 404
        assert client.post("/api/team", json={"name": "旧团队"}).status_code == 405
        assert client.post("/api/playbook-cards/extract", json={"session_id": "old"}).status_code == 405

        persona = make_persona(id="old_persona")
        scenario = make_scenario(id="old_team_scenario", persona_id=persona.id, team_id="old_team")
        repo.save(persona)
        repo.save(scenario)
        repo.save(Session(id="old_session", scenario_id=scenario.id, rep_id=owner_id,
                          started_at=datetime.now(UTC)))
        assert client.get("/api/scenarios/old_team_scenario").status_code == 200
        assert client.get("/api/sessions/old_session").status_code == 200
        assert client.post("/api/sessions", json={"scenario_id": scenario.id}).status_code == 404
        assert scenario.id not in [item["id"] for item in client.get("/api/scenarios").json()]
        assert other.get("/api/scenarios/old_team_scenario").status_code == 404
    finally:
        app.dependency_overrides.clear()
