import json
from uuid import uuid4

import pytest
from app.db import Repo
from app.deps import get_provider, get_repo
from app.llm import MockLLM
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture()
def clients(tmp_path):
    repo = Repo(f"sqlite:///{tmp_path}/diary.db")
    digest = {"summary": "我第一次感到沟通太急。", "first_impressions": ["我当时很紧张"],
              "doctor_feedback": ["医生说不喜欢性价比这个词"], "what_to_improve": ["先问对方关注点"],
              "next_visit": ["准备正式资料"], "uncertain_claims": []}
    mock = MockLLM({"field_diary": json.dumps(digest, ensure_ascii=False)})
    app.dependency_overrides[get_repo] = lambda: repo
    app.dependency_overrides[get_provider] = lambda: mock
    test_ip = str(uuid4())
    first = TestClient(app, headers={"x-real-ip": test_ip})
    second = TestClient(app, headers={"x-real-ip": test_ip})
    assert first.post("/api/auth/register", json={"username": "diaryone", "password": "long-password-123"}).status_code == 200
    assert second.post("/api/auth/register", json={"username": "diarytwo", "password": "long-password-456"}).status_code == 200
    yield first, second, mock
    app.dependency_overrides.clear()


def test_diary_keeps_raw_words_and_separates_accounts(clients):
    first, second, mock = clients
    raw = "  今天主任说他不喜欢性价比这个词，我当时很紧张。  "
    response = first.post("/api/diary", json={"hospital": "某医院", "doctor_name": "某主任", "raw_text": raw})
    assert response.status_code == 200
    item = response.json()
    assert item["raw_text"] == raw.strip()
    assert item["digest"]["first_impressions"] == ["我当时很紧张"]
    assert item["degraded"] is False and item["review_status"] == "unreviewed"
    assert len([call for call in mock.calls if call["prompt_name"] == "field_diary"]) == 1
    assert [entry["id"] for entry in first.get("/api/diary").json()] == [item["id"]]
    assert second.get("/api/diary").json() == []
    assert second.get(f"/api/diary/{item['id']}").status_code == 404
    assert second.delete(f"/api/diary/{item['id']}").status_code == 404
    assert first.get(f"/api/diary/{item['id']}").json()["raw_text"] == raw.strip()
    assert first.delete(f"/api/diary/{item['id']}").json() == {"ok": True}
    assert first.get(f"/api/diary/{item['id']}").status_code == 404


def test_diary_preserves_note_when_model_output_is_invalid(clients):
    first, _, mock = clients
    mock.set("field_diary", "not JSON")
    response = first.post("/api/diary", json={"raw_text": "拜访结束后，我想先记下医生提出的问题。"})
    assert response.status_code == 200
    item = response.json()
    assert item["degraded"] is True
    assert item["digest"]["summary"] == item["raw_text"]
