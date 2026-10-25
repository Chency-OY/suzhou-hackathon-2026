import pytest
from app.db import Repo
from app.deps import get_repo
from app.main import app
from app.personas import build_demo_personas
from fastapi.testclient import TestClient

from tests.factories import make_scenario


@pytest.fixture()
def client(tmp_path):
    repo = Repo(f"sqlite:///{tmp_path}/api.db")
    personas = build_demo_personas()
    for p in personas:
        repo.save(p)
    repo.save(make_scenario(id="scn_001", persona_id=personas[0].id, type="first_visit"))
    repo.save(make_scenario(id="scn_002", persona_id=personas[2].id, type="competitor_compare"))
    repo.save(make_scenario(id="scn_003", persona_id=personas[6].id, type="off_label_bait"))
    app.dependency_overrides[get_repo] = lambda: repo
    yield TestClient(app), personas
    app.dependency_overrides.clear()


def test_list_and_filters(client):
    c, _ = client
    assert len(c.get("/api/scenarios").json()) == 3
    assert [s["id"] for s in c.get("/api/scenarios", params={"dept": "hepatology"}).json()] == ["scn_003"]
    assert [s["id"] for s in c.get("/api/scenarios", params={"difficulty": "hard"}).json()] == ["scn_002"]
    assert [s["id"] for s in c.get("/api/scenarios", params={"type": "first_visit"}).json()] == ["scn_001"]


def test_detail_has_public_persona_only(client):
    c, personas = client
    r = c.get("/api/scenarios/scn_001")
    assert r.status_code == 200
    body = r.json()
    assert set(body["persona_public"]) == {"department", "title", "hospital_tier", "style_hint", "difficulty"}
    text = r.text
    for secret in (personas[0].hidden_objection, "hidden_objection", "traps", "initial_trust"):
        assert secret not in text


def test_list_never_leaks_secrets(client):
    c, personas = client
    text = c.get("/api/scenarios").text
    assert all(p.hidden_objection not in text for p in personas) and "hidden_objection" not in text


def test_404(client):
    c, _ = client
    assert c.get("/api/scenarios/nope").status_code == 404
