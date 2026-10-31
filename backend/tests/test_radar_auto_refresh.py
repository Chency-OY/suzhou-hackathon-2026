from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
from app.db import Repo
from app.deps import get_provider, get_repo
from app.llm import MockLLM
from app.main import app
from app.models.radar import AcademicRadar
from app.radar.openalex import radar_id
from fastapi.testclient import TestClient


def _record(owner_id: str, name: str, *, enabled: bool = True) -> AcademicRadar:
    return AcademicRadar(id=radar_id(owner_id, name, "某某医院"), owner_id=owner_id,
                         doctor_name=name, hospital="某某医院", searched_at=datetime.now(UTC) - timedelta(days=2),
                         status="no_match", web_status="ok", auto_refresh=enabled)


def _clients(tmp_path):
    repo = Repo(f"sqlite:///{tmp_path}/radar-auto.db")
    app.dependency_overrides[get_repo] = lambda: repo
    app.dependency_overrides[get_provider] = lambda: MockLLM()
    first = TestClient(app, headers={"x-real-ip": str(uuid4())})
    second = TestClient(app, headers={"x-real-ip": str(uuid4())})
    first_id = first.post("/api/auth/register", json={"username": "autofirst", "password": "long-password-123"}).json()["id"]
    second_id = second.post("/api/auth/register", json={"username": "autosecond", "password": "long-password-456"}).json()["id"]
    return repo, first, second, first_id, second_id


def test_open_page_refreshes_only_opted_in_own_due_records(tmp_path, monkeypatch):
    repo, first, second, first_id, second_id = _clients(tmp_path)
    try:
        for name in ("甲某", "乙某", "丙某", "丁某"):
            repo.save(_record(first_id, name))
        repo.save(_record(first_id, "戊某", enabled=False))
        repo.save(_record(second_id, "己某"))
        calls = []

        def fake_collect(repo_arg, owner_id, doctor_name, hospital, provider, cached):
            calls.append((owner_id, doctor_name, hospital))
            return cached.model_copy(update={"searched_at": datetime.now(UTC), "web_status": "ok"})

        monkeypatch.setattr("app.radar.auto_refresh.collect_radar", fake_collect)
        refreshed = first.post("/api/radar/refresh-due")
        assert refreshed.status_code == 200
        assert len(refreshed.json()) == 3
        assert len(calls) == 3 and all(owner == first_id for owner, _, _ in calls)
        assert repo.get(AcademicRadar, radar_id(first_id, "戊某", "某某医院")).last_auto_checked_at is None
        assert repo.get(AcademicRadar, radar_id(second_id, "己某", "某某医院")).last_auto_checked_at is None
        assert len(second.post("/api/radar/refresh-due").json()) == 1
        assert calls[-1][0] == second_id
    finally:
        app.dependency_overrides.clear()


def test_opt_in_is_private_and_failed_refresh_keeps_old_result(tmp_path, monkeypatch):
    repo, first, second, first_id, _ = _clients(tmp_path)
    try:
        record = _record(first_id, "甲某", enabled=False)
        repo.save(record)
        path = f"/api/radar/{record.id}/auto-refresh"
        assert second.patch(path, json={"enabled": True}).status_code == 404
        assert first.post("/api/radar/refresh-due").json() == []
        assert first.patch(path, json={"enabled": True}).json()["auto_refresh"] is True

        def unavailable(*args):
            raise RuntimeError("synthetic outage")

        monkeypatch.setattr("app.radar.auto_refresh.collect_radar", unavailable)
        result = first.post("/api/radar/refresh-due").json()[0]
        assert datetime.fromisoformat(result["searched_at"]) == record.searched_at
        assert result["refresh_error"] and result["last_auto_checked_at"]
        assert first.post("/api/radar/refresh-due").json() == []
        assert first.patch(path, json={"enabled": False}).json()["auto_refresh"] is False
    finally:
        app.dependency_overrides.clear()


def test_web_outage_keeps_existing_sources(tmp_path, monkeypatch):
    repo, first, _, first_id, _ = _clients(tmp_path)
    try:
        record = _record(first_id, "甲某")
        record.note = "上次有可核对的网页来源"
        repo.save(record)

        def unavailable(*args):
            raise httpx.ConnectError("web unavailable")

        def should_not_search_academic(*args):
            raise AssertionError("existing result must be preserved")

        monkeypatch.setattr("app.api.radar.search_web", unavailable)
        monkeypatch.setattr("app.api.radar.search_academic", should_not_search_academic)
        result = first.post("/api/radar/refresh-due").json()[0]
        assert result["note"] == record.note
        assert datetime.fromisoformat(result["searched_at"]) == record.searched_at
        assert result["refresh_error"]
    finally:
        app.dependency_overrides.clear()
