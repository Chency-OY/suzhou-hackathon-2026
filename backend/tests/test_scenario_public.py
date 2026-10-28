import pytest
from app.db import Repo
from app.deps import get_repo
from app.main import app
from app.personas import build_demo_personas
from fastapi.testclient import TestClient

from tests.factories import make_scenario

DEMO = build_demo_personas()
INTERNAL = ["内部计划X", "内部要点Y", "内部检查Z", "内部事件W", "baits", "turn_plan", "gold_moves",
            "compliance_checks", "events", "hidden_objection", "traps"]


@pytest.fixture()
def client(tmp_path):
    repo = Repo(f"sqlite:///{tmp_path}/p.db")
    for p in DEMO:
        repo.save(p)
    repo.save(make_scenario(
        id="scn_001", persona_id=DEMO[1].id, type="hard_refusal", skeleton_id="S04", pre_info="前情A",
        setting={"where": "科室", "duration": "5分钟"}, hard_gate=True, post_task="写拜访记录",
        turn_plan=["内部计划X"], gold_moves=["内部要点Y"], compliance_checks=["内部检查Z"],
        events=["内部事件W"], baits=["off_label_bait"]))
    app.dependency_overrides[get_repo] = lambda: repo
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_public_api_hides_internal_fields(client):
    for url in ("/api/scenarios", "/api/scenarios/scn_001"):
        text = client.get(url).text
        for secret in INTERNAL:
            assert secret not in text, (url, secret)


def test_public_fields_are_present(client):
    d = client.get("/api/scenarios/scn_001").json()
    assert d["pre_info"] == "前情A" and d["skeleton_id"] == "S04" and d["hard_gate"] is True
    assert d["post_task"] == "写拜访记录" and d["setting"]["duration"] == "5分钟"
