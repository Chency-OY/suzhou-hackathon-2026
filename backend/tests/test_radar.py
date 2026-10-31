from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

import httpx
from app.db import Repo
from app.deps import get_provider, get_repo
from app.llm import MockLLM
from app.main import app
from app.models.radar import AcademicRadar, RadarWebSource
from app.radar.openalex import _name_matches, _search_name, radar_id, search_academic
from fastapi.testclient import TestClient


def test_chinese_name_is_romanized_but_stays_identity_candidate():
    assert _search_name("张伟") == "Zhang Wei"
    assert _name_matches("Zhang Wei", "Wei Zhang")
    assert not _name_matches("Zhang Wei", "Weiguo Zhang")

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/institutions":
            body = {"results": [{"id": "https://openalex.org/I1", "display_name": "Soochow Hospital",
                                 "display_name_alternatives": ["苏州大学附属第一医院"]}]}
        elif request.url.path == "/authors":
            body = {"results": [{"id": "https://openalex.org/A1", "display_name": "Wei Zhang"}]}
        else:
            matching = {"author": {"id": "https://openalex.org/A1", "display_name": "Wei Zhang"},
                        "institutions": [{"id": "https://openalex.org/I1"}]}
            wrong_affiliation = {"author": {"id": "https://openalex.org/A1", "display_name": "Wei Zhang"},
                                 "institutions": [{"id": "https://openalex.org/I2"}]}
            body = {"results": [
                {"id": "https://openalex.org/W1", "display_name": "Matched paper", "publication_date": "2026-01-01",
                 "doi": "https://doi.org/10.1234/test", "primary_location": {"source": {"display_name": "Journal"}},
                 "authorships": [matching]},
                {"id": "https://openalex.org/W2", "display_name": "Wrong hospital", "publication_date": "2026-01-01",
                 "doi": "https://doi.org/10.1234/other", "authorships": [wrong_affiliation]},
            ]}
        return httpx.Response(200, text=json.dumps(body))

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result = search_academic("owner", "张伟", "苏州大学附属第一医院", client)
    assert result.status == "found"
    assert [work.title for work in result.works] == ["Matched paper"]
    assert result.works[0].identity_status == "candidate"
    assert result.works[0].url == "https://doi.org/10.1234/test"


def test_inexact_hospital_is_not_treated_as_verified_match():
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/institutions"
        return httpx.Response(200, json={"results": [{"id": "https://openalex.org/I1",
                                                   "display_name": "Another Hospital",
                                                   "display_name_alternatives": []}]})

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result = search_academic("owner", "张伟", "苏州大学附属第一医院", client)
    assert result.status == "ambiguous_institution" and result.works == []


def test_radar_cache_and_account_isolation(tmp_path, monkeypatch):
    repo = Repo(f"sqlite:///{tmp_path}/radar.db")
    app.dependency_overrides[get_repo] = lambda: repo
    calls = []

    def fake_search(owner_id: str, doctor_name: str, hospital: str) -> AcademicRadar:
        calls.append(owner_id)
        return AcademicRadar(id=radar_id(owner_id, doctor_name, hospital), owner_id=owner_id,
                             doctor_name=doctor_name, hospital=hospital,
                             searched_at=datetime.now(UTC), status="no_match")

    monkeypatch.setattr("app.api.radar.search_academic", fake_search)
    first = TestClient(app, headers={"x-real-ip": str(uuid4())})
    second = TestClient(app, headers={"x-real-ip": str(uuid4())})
    try:
        assert first.post("/api/auth/register", json={"username": "radarone", "password": "long-password-123"}).status_code == 200
        assert second.post("/api/auth/register", json={"username": "radartwo", "password": "long-password-456"}).status_code == 200
        body = {"doctor_name": "张伟", "hospital": "苏州大学附属第一医院"}
        first_result = first.post("/api/radar/search", json=body)
        assert first_result.status_code == 200
        assert first_result.json()["auto_refresh"] is False
        assert first.post("/api/radar/search", json=body).status_code == 200
        assert len(calls) == 1
        assert len(first.get("/api/radar").json()) == 1
        assert second.get("/api/radar").json() == []
    finally:
        app.dependency_overrides.clear()


def test_deepseek_answer_is_account_scoped_and_cached(tmp_path, monkeypatch):
    repo = Repo(f"sqlite:///{tmp_path}/web-radar.db")
    app.dependency_overrides[get_repo] = lambda: repo
    quote = "甲某来自某某医院并参加公开学术会议"
    model = MockLLM({"radar_answer": json.dumps({"points": [{"kind": "conference",
        "statement": "找到一条待确认的会议线索。", "source_id": "web_1", "evidence_quote": quote}]}, ensure_ascii=False)})
    app.dependency_overrides[get_provider] = lambda: model
    calls = []

    def fake_web(name, hospital):
        calls.append((name, hospital))
        source = RadarWebSource(id="web_1", kind="conference", title="会议日程",
                                url="https://example.org/meeting", name_in_source=True,
                                hospital_in_source=True)
        return [source], {"web_1": quote}, "ok"

    def fake_openalex(owner_id, doctor_name, hospital):
        return AcademicRadar(id=radar_id(owner_id, doctor_name, hospital), owner_id=owner_id,
                             doctor_name=doctor_name, hospital=hospital,
                             searched_at=datetime.now(UTC), status="no_match")

    monkeypatch.setattr("app.api.radar.search_web", fake_web)
    monkeypatch.setattr("app.api.radar.search_academic", fake_openalex)
    first = TestClient(app, headers={"x-real-ip": str(uuid4())})
    second = TestClient(app, headers={"x-real-ip": str(uuid4())})
    try:
        assert first.post("/api/auth/register", json={"username": "webone", "password": "long-password-123"}).status_code == 200
        assert second.post("/api/auth/register", json={"username": "webtwo", "password": "long-password-456"}).status_code == 200
        body = {"doctor_name": "甲某", "hospital": "某某医院"}
        result = first.post("/api/radar/search", json=body).json()
        assert result["web_status"] == "ok" and result["radar_version"]
        assert result["answer_points"][0]["evidence_quote"] == quote
        assert result["web_sources"][0]["identity_status"] == "candidate"
        assert first.post("/api/radar/search", json=body).json()["id"] == result["id"]
        assert len(calls) == 1 and len(model.calls) == 1
        assert second.get("/api/radar").json() == []
    finally:
        app.dependency_overrides.clear()
