import json
from datetime import UTC, datetime

import pytest
from app.academic_crosscheck import compare_academic
from app.db import Repo
from app.deps import get_provider, get_repo
from app.llm import MockLLM
from app.main import app
from app.models.diary import AcademicCrosscheck, DiaryDigest, FieldDiary
from app.models.radar import AcademicRadar, RadarAnswerPoint, RadarWebSource
from app.radar.openalex import radar_id
from fastapi.testclient import TestClient

RAW = "甲医生说他从未在星河论坛做过学术报告。"
SOURCE = "甲医生在星河论坛做了主题报告，介绍研究过程。"


def _diary(owner_id: str) -> FieldDiary:
    return FieldDiary(id="diary_synthetic", owner_id=owner_id, created_at=datetime.now(UTC),
                      doctor_name="甲医生", hospital="某某医院", raw_text=RAW,
                      digest=DiaryDigest(summary="虚构拜访回忆"))


def _radar(owner_id: str) -> AcademicRadar:
    return AcademicRadar(id=radar_id(owner_id, "甲医生", "某某医院"), owner_id=owner_id,
                         doctor_name="甲医生", hospital="某某医院", searched_at=datetime.now(UTC),
                         status="found", web_status="ok", radar_version="deepseek-web-v1",
                         web_sources=[RadarWebSource(id="web_1", kind="conference", title="星河论坛日程",
                                                     url="https://example.org/forum", name_in_source=True,
                                                     hospital_in_source=True)],
                         answer_points=[RadarAnswerPoint(kind="conference", statement="待核对的论坛发言线索",
                                                         source_id="web_1", evidence_quote=SOURCE)])


def _mock(quote: str = RAW, source_quote: str = SOURCE) -> MockLLM:
    return MockLLM({"academic_crosscheck": json.dumps({"tensions": [{"diary_quote": quote,
        "source_id": "web_1", "source_quote": source_quote}]}, ensure_ascii=False)})


def test_crosscheck_needs_both_exact_quotes_and_keeps_identity_uncertain():
    diary, radar = _diary("synthetic_user"), _radar("synthetic_user")
    mock = _mock()
    result = compare_academic(diary, radar, mock)
    assert result.status == "compared" and len(result.tensions) == 1
    assert result.tensions[0].source_url == "https://example.org/forum"
    assert "身份" in result.tensions[0].note
    assert RAW in mock.calls[0]["messages"][0]["content"]
    assert compare_academic(diary, radar, _mock("日记中不存在的论断", SOURCE)).tensions == []
    assert compare_academic(diary, radar, _mock(RAW, "网页中不存在的论断")).tensions == []


def test_no_radar_or_medical_statement_never_creates_academic_tension():
    diary = _diary("synthetic_user")
    mock = _mock()
    assert compare_academic(diary, None, mock).status == "no_radar" and mock.calls == []
    diary.raw_text = "甲医生说某药治疗患者有效。"
    result = compare_academic(diary, _radar("synthetic_user"),
                              _mock("甲医生说某药治疗患者有效。", SOURCE))
    assert result.tensions == []


@pytest.fixture()
def clients(tmp_path):
    repo = Repo(f"sqlite:///{tmp_path}/crosscheck.db")
    mock = _mock()
    app.dependency_overrides[get_repo] = lambda: repo
    app.dependency_overrides[get_provider] = lambda: mock
    owner, other = TestClient(app), TestClient(app)
    owner.headers["x-real-ip"] = "198.51.100.80"
    other.headers["x-real-ip"] = "198.51.100.81"
    owner_id = owner.post("/api/auth/register", json={"username": "crossowner", "password": "test-password-123"}).json()["id"]
    other.post("/api/auth/register", json={"username": "crossother", "password": "test-password-123"})
    repo.save(_diary(owner_id))
    repo.save(_radar(owner_id))
    yield repo, mock, owner, other, owner_id
    app.dependency_overrides.clear()


def test_crosscheck_is_private_cached_and_invalidated_by_radar_refresh(clients):
    repo, mock, owner, other, owner_id = clients
    path = "/api/diary/diary_synthetic/academic-crosscheck"
    assert other.post(path).status_code == 404
    first = owner.post(path)
    assert first.status_code == 200 and len(first.json()["tensions"]) == 1
    assert owner.get(path).status_code == 200
    assert owner.post(path).status_code == 200 and len(mock.calls) == 1
    radar = _radar(owner_id)
    radar.searched_at = datetime.now(UTC)
    repo.save(radar)
    assert owner.get(path).status_code == 404
    assert owner.post(path).status_code == 200 and len(mock.calls) == 2
    assert owner.delete("/api/diary/diary_synthetic").status_code == 200
    assert repo.get(AcademicCrosscheck, "academic_diary_synthetic") is None
