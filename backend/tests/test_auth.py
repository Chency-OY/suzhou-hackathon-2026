import pytest
from app.db import Repo
from app.deps import get_repo
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path):
    repo = Repo(f"sqlite:///{tmp_path}/auth.db")
    app.dependency_overrides[get_repo] = lambda: repo
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_register_login_logout(client):
    assert client.get("/api/auth/me").status_code == 401
    registered = client.post("/api/auth/register", json={"username": "Pilot_01", "password": "long-password-123"})
    assert registered.status_code == 200
    assert registered.json()["username"] == "pilot_01"
    assert "httponly" in registered.headers["set-cookie"].lower()
    assert client.get("/api/auth/check").status_code == 204
    assert client.get("/api/auth/me").json() == registered.json()
    assert client.post("/api/auth/logout").json() == {"ok": True}
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/auth/login", json={"username": "pilot_01", "password": "wrong-password"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "pilot_01", "password": "long-password-123"}).status_code == 200
    assert client.get("/api/auth/me").json() == registered.json()


def test_invalid_and_duplicate_registration(client):
    assert client.post("/api/auth/register", json={"username": "bad space", "password": "long-password"}).status_code == 422
    assert client.post("/api/auth/register", json={"username": "pilot02", "password": "short"}).status_code == 422
    body = {"username": "pilot02", "password": "long-password"}
    assert client.post("/api/auth/register", json=body).status_code == 200
    assert client.post("/api/auth/register", json=body).status_code == 409
