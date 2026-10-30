from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from ..db import Repo
from ..deps import get_provider, get_repo
from ..llm import LLMProvider, load_prompt, structured_call
from ..models.auth import Account
from ..models.diary import DiaryDigest, DiaryReview, FieldDiary
from ..models.radar import AcademicRadar
from ..radar.openalex import radar_id
from ..tribunal import assess_claim, extract_claims
from .auth import _rate_limit, get_current_account

router = APIRouter(prefix="/api/diary")
log = logging.getLogger(__name__)


class NewDiary(BaseModel):
    hospital: str = Field(default="", max_length=120)
    doctor_name: str = Field(default="", max_length=80)
    raw_text: str = Field(min_length=8, max_length=4000)

    @field_validator("hospital", "doctor_name", "raw_text")
    @classmethod
    def trim(cls, value: str) -> str:
        return value.strip()


def _not_found() -> HTTPException:
    return HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "日记不存在"}})


def _own_diary(repo: Repo, diary_id: str, account: Account) -> FieldDiary:
    item = repo.get(FieldDiary, diary_id)
    if not item or item.owner_id != account.id:
        raise _not_found()
    return item


def _fallback(raw_text: str) -> DiaryDigest:
    return DiaryDigest(summary=raw_text[:160], uncertain_claims=["AI 暂不可用；请按原话自行核对。"])


def _digest(raw_text: str, provider: LLMProvider) -> tuple[DiaryDigest, bool]:
    if provider.name == "mock" and not provider.responses:
        return _fallback(raw_text), True
    prompt = load_prompt("field_diary").render(raw_text=raw_text)
    try:
        return structured_call(
            provider, prompt_name="field_diary", system="你只输出符合要求的 JSON 日记，不编造事实。",
            messages=[{"role": "user", "content": prompt}], model_cls=DiaryDigest,
            fallback=lambda: _fallback(raw_text), max_retries=1, temperature=0.2, max_tokens=850,
        )
    except RuntimeError as exc:
        log.warning("前线日记整理暂不可用，保留原话：%s", exc)
        return _fallback(raw_text), True


@router.post("", response_model=FieldDiary)
def create_diary(body: NewDiary, repo: Repo = Depends(get_repo), account: Account = Depends(get_current_account),
                 provider: LLMProvider = Depends(get_provider)):
    digest, degraded = _digest(body.raw_text, provider)
    item = FieldDiary(id=f"diary_{uuid4().hex}", owner_id=account.id, created_at=datetime.now(UTC),
                      hospital=body.hospital, doctor_name=body.doctor_name,
                      raw_text=body.raw_text, digest=digest, degraded=degraded)
    repo.save(item)
    return item


@router.get("", response_model=list[FieldDiary])
def list_diary(repo: Repo = Depends(get_repo), account: Account = Depends(get_current_account)):
    items = (item for item in repo.list(FieldDiary) if item.owner_id == account.id)
    return sorted(items, key=lambda item: item.created_at, reverse=True)[:100]


@router.get("/{diary_id}", response_model=FieldDiary)
def get_diary(diary_id: str, repo: Repo = Depends(get_repo), account: Account = Depends(get_current_account)):
    return _own_diary(repo, diary_id, account)


@router.get("/{diary_id}/review", response_model=DiaryReview)
def get_review(diary_id: str, repo: Repo = Depends(get_repo), account: Account = Depends(get_current_account)):
    _own_diary(repo, diary_id, account)
    review = repo.get(DiaryReview, f"review_{diary_id}")
    if not review or review.owner_id != account.id:
        raise _not_found()
    return review


@router.post("/{diary_id}/review", response_model=DiaryReview)
def review_diary(diary_id: str, request: Request, refresh: bool = False, repo: Repo = Depends(get_repo),
                 account: Account = Depends(get_current_account), provider: LLMProvider = Depends(get_provider)):
    item = _own_diary(repo, diary_id, account)
    key = f"review_{diary_id}"
    cached = repo.get(DiaryReview, key)
    if cached and not refresh and datetime.now(UTC) - cached.reviewed_at < timedelta(hours=24):
        return cached
    _rate_limit(request, "diary_review", account.id, 20, 3600)
    radar = repo.get(AcademicRadar, radar_id(account.id, item.doctor_name, item.hospital)) if (
        item.doctor_name and item.hospital) else None
    review = DiaryReview(id=key, diary_id=diary_id, owner_id=account.id, reviewed_at=datetime.now(UTC),
                         findings=[assess_claim(claim, provider) for claim in extract_claims(item)],
                         academic_candidate_count=len(radar.works) if radar else 0)
    repo.save(review)
    return review


@router.delete("/{diary_id}")
def delete_diary(diary_id: str, repo: Repo = Depends(get_repo), account: Account = Depends(get_current_account)):
    _own_diary(repo, diary_id, account)
    repo.delete(DiaryReview, f"review_{diary_id}")
    repo.delete(FieldDiary, diary_id)
    return {"ok": True}
