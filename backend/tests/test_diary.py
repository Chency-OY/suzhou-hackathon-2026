import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.db import Repo
from app.deps import get_provider, get_repo
from app.llm import MockLLM
from app.main import app
from app.models.diary import DiaryReview
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


def test_long_diary_preserves_full_transcript_and_summarizes_the_end(clients):
    first, _, mock = clients
    raw = "拜访后我想记录今天沟通的细节。" * 420 + "最后我决定下次先倾听问题，再准备正式资料。"

    def digest_segment(messages):
        content = messages[-1]["content"]
        last = "最后我决定" in content
        return json.dumps({"summary": "最后要先倾听并准备资料" if last else "拜访中的沟通记录",
                           "first_impressions": [], "doctor_feedback": [],
                           "what_to_improve": [], "next_visit": [], "uncertain_claims": []}, ensure_ascii=False)

    mock.set("field_diary", digest_segment)
    response = first.post("/api/diary", json={"raw_text": raw})
    assert response.status_code == 200
    item = response.json()
    assert item["raw_text"] == raw
    assert "最后要先倾听" in item["digest"]["summary"]
    assert len([call for call in mock.calls if call["prompt_name"] == "field_diary"]) >= 2
    assert first.get(f"/api/diary/{item['id']}").json()["raw_text"].endswith("正式资料。")


def test_diary_rejects_text_beyond_long_form_limit(clients):
    first, _, mock = clients
    assert first.post("/api/diary", json={"raw_text": "记" * 16001}).status_code == 422
    assert first.get("/api/diary").json() == []
    assert mock.calls == []


@pytest.mark.parametrize("raw", ["患者手机号是13800000000，请记录。", "患者身份证号110101199001011234，请记录。",
                                     "请联系patient@example.com获取信息。"])
def test_obvious_identifiers_are_rejected_before_diary_storage(clients, raw):
    first, _, mock = clients
    assert first.post("/api/diary", json={"raw_text": raw}).status_code == 422
    assert first.get("/api/diary").json() == []
    assert mock.calls == []


def test_review_is_private_cached_and_deleted_with_diary(clients):
    first, second, mock = clients
    digest = {"summary": "拜访后回忆", "first_impressions": ["我很紧张"],
              "doctor_feedback": [], "what_to_improve": [], "next_visit": [],
              "uncertain_claims": ["信尔美没有副作用"]}
    mock.set("field_diary", json.dumps(digest, ensure_ascii=False))
    mock.set("diary_tribunal", "not JSON")
    item = first.post("/api/diary", json={"raw_text": "今天有人说信尔美没有副作用，我想核对资料。"}).json()
    path = f"/api/diary/{item['id']}/review"
    assert second.post(path).status_code == 404
    response = first.post(path)
    assert response.status_code == 200
    review = response.json()
    assert review["findings"][0]["status"] == "insufficient"
    assert review["findings"][0]["candidates"]
    calls = len([call for call in mock.calls if call["prompt_name"] == "diary_tribunal"])
    assert first.post(path).json()["id"] == review["id"]
    assert len([call for call in mock.calls if call["prompt_name"] == "diary_tribunal"]) == calls
    assert second.get(path).status_code == 404
    assert first.get(path).json()["id"] == review["id"]
    assert first.delete(f"/api/diary/{item['id']}").status_code == 200
    assert first.get(path).status_code == 404


def test_review_does_not_judge_hallucinated_digest_claim(clients):
    first, _, mock = clients
    digest = {"summary": "拜访后回忆", "first_impressions": [], "doctor_feedback": [],
              "what_to_improve": [], "next_visit": [], "uncertain_claims": ["信尔美没有副作用"]}
    mock.set("field_diary", json.dumps(digest, ensure_ascii=False))
    item = first.post("/api/diary", json={"raw_text": "今天主任问我能否提供正式说明书，暂时没有谈具体药物。"}).json()
    review = first.post(f"/api/diary/{item['id']}/review").json()
    finding = review["findings"][0]
    assert finding["status"] == "insufficient" and finding["grounded_in_raw"] is False
    assert not [call for call in mock.calls if call["prompt_name"] == "diary_tribunal"]


def test_old_or_expired_review_must_be_recomputed(clients):
    first, _, _ = clients
    item = first.post("/api/diary", json={"raw_text": "今天主任让我先把正式资料留下，改天再谈。"}).json()
    path = f"/api/diary/{item['id']}/review"
    first.post(path)
    repo = app.dependency_overrides[get_repo]()
    stored = repo.get(DiaryReview, f"review_{item['id']}")
    assert stored is not None
    stored.policy_version = "older-policy"
    repo.save(stored)
    assert first.get(path).status_code == 404
    current = first.post(path).json()
    assert current["policy_version"] != "older-policy"
    stored = repo.get(DiaryReview, current["id"])
    assert stored is not None
    stored.reviewed_at = datetime.now(UTC) - timedelta(hours=25)
    repo.save(stored)
    assert first.get(path).status_code == 404
    assert first.post(path).json()["reviewed_at"] != stored.reviewed_at.isoformat()
