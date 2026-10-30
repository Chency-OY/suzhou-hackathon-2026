from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

import httpx
from app.db import Repo
from app.deps import get_repo
from app.main import app
from app.models.radar import AcademicRadar
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
        assert first.post("/api/radar/search", json=body).status_code == 200
        assert first.post("/api/radar/search", json=body).status_code == 200
        assert len(calls) == 1
        assert len(first.get("/api/radar").json()) == 1
        assert second.get("/api/radar").json() == []
    finally:
        app.dependency_overrides.clear()
