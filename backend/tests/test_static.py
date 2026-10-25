from app.static import mount_frontend
from fastapi import FastAPI
from fastapi.testclient import TestClient


def make_app(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text('<div id="root"></div>', encoding="utf-8")
    (tmp_path / "assets" / "a.js").write_text("console.log(1)", encoding="utf-8")
    (tmp_path / "favicon.svg").write_text("<svg/>", encoding="utf-8")
    app = FastAPI()

    @app.get("/api/ping")
    def ping():
        return {"ok": True}

    assert mount_frontend(app, tmp_path) is True
    return TestClient(app)


def test_spa_fallback_assets_and_api(tmp_path):
    c = make_app(tmp_path)
    assert c.get("/api/ping").json() == {"ok": True}
    assert 'id="root"' in c.get("/scenarios/scn_001").text
    assert c.get("/assets/a.js").status_code == 200
    assert c.get("/favicon.svg").text == "<svg/>"
    r = c.get("/api/missing")
    assert r.status_code == 404 and "root" not in r.text


def test_no_path_traversal(tmp_path):
    c = make_app(tmp_path)
    r = c.get("/%2e%2e/%2e%2e/etc/passwd")
    assert "root:x" not in r.text


def test_returns_false_without_build(tmp_path):
    assert mount_frontend(FastAPI(), tmp_path) is False
