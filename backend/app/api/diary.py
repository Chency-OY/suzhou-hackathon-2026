from __future__ import annotations

import logging
import re
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from ..academic_crosscheck import POLICY_VERSION, compare_academic
from ..db import Repo
from ..deps import get_provider, get_repo
from ..llm import LLMProvider, load_prompt, structured_call
from ..models.auth import Account
from ..models.diary import AcademicCrosscheck, DiaryDigest, DiaryPreview, DiaryReview, FieldDiary
from ..models.radar import AcademicRadar
from ..radar.openalex import radar_id
from ..tribunal import assess_claim, extract_claims
from .auth import _rate_limit, get_current_account, is_guest_account

router = APIRouter(prefix="/api/diary")
log = logging.getLogger(__name__)
REVIEW_POLICY_VERSION = "2026-10-31-grounded-label"
MAX_DIARY_CHARS = 16000
DIARY_CHUNK_CHARS = 4200
_OBVIOUS_IDENTIFIER = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)|(?<!\d)\d{17}[\dXx](?!\w)|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


class NewDiary(BaseModel):
    hospital: str = Field(default="", max_length=120)
    doctor_name: str = Field(default="", max_length=80)
    raw_text: str = Field(min_length=8, max_length=MAX_DIARY_CHARS)

    @field_validator("hospital", "doctor_name", "raw_text")
    @classmethod
    def trim(cls, value: str) -> str:
        value = value.strip()
        if _OBVIOUS_IDENTIFIER.search(value):
            raise ValueError("请删除手机号、身份证号或邮箱后再保存日记")
        return value


def _not_found() -> HTTPException:
    return HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "日记不存在"}})


def _own_diary(repo: Repo, diary_id: str, account: Account) -> FieldDiary:
    item = repo.get(FieldDiary, diary_id)
    if not item or item.owner_id != account.id:
        raise _not_found()
    return item


def _matching_radar(repo: Repo, item: FieldDiary, account: Account) -> AcademicRadar | None:
    if not item.doctor_name or not item.hospital:
        return None
    radar = repo.get(AcademicRadar, radar_id(account.id, item.doctor_name, item.hospital))
    if not radar or radar.owner_id != account.id or radar.web_status != "ok":
        return None
    return radar if datetime.now(UTC) - radar.searched_at < timedelta(hours=24) else None


def _valid_academic_cache(repo: Repo, item: FieldDiary, account: Account) -> AcademicCrosscheck | None:
    cached = repo.get(AcademicCrosscheck, f"academic_{item.id}")
    radar = _matching_radar(repo, item, account)
    if (cached and cached.owner_id == account.id and cached.policy_version == POLICY_VERSION
            and datetime.now(UTC) - cached.checked_at < timedelta(hours=24)
            and cached.radar_id == (radar.id if radar else "")
            and (not radar or radar.searched_at <= cached.checked_at)):
        return cached
    return None


def _fallback(raw_text: str) -> DiaryDigest:
    return DiaryDigest(summary=raw_text[:160], uncertain_claims=["AI 暂不可用；请按原话自行核对。"])


def _diary_chunks(raw_text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(raw_text):
        end = min(start + DIARY_CHUNK_CHARS, len(raw_text))
        if end < len(raw_text):
            boundary = max(raw_text.rfind(mark, start + 2800, end) for mark in "。！？\n")
            if boundary > start:
                end = boundary + 1
        chunks.append(raw_text[start:end])
        start = end
    return chunks


def _merge_digests(parts: list[DiaryDigest]) -> DiaryDigest:
    per_part = max(40, 480 // len(parts) - 1)
    summary = "；".join(part.summary[:per_part] for part in parts)[:500]
    fields = {}
    for name in ("first_impressions", "doctor_feedback", "what_to_improve", "next_visit", "uncertain_claims"):
        selected = []
        for index in range(6):
            for part in parts:
                values = getattr(part, name)
                if index < len(values) and values[index] not in selected:
                    selected.append(values[index])
                    if len(selected) == 6:
                        break
            if len(selected) == 6:
                break
        fields[name] = selected
    names = {part.doctor_name.strip() for part in parts if part.doctor_name.strip()}
    hospitals = {part.hospital.strip() for part in parts if part.hospital.strip()}
    return DiaryDigest(summary=summary, doctor_name=next(iter(names)) if len(names) == 1 else "",
                       hospital=next(iter(hospitals)) if len(hospitals) == 1 else "", **fields)


def _grounded_context(value: str, raw_text: str) -> str:
    value = value.strip()
    return value if value and value in raw_text and not _OBVIOUS_IDENTIFIER.search(value) else ""


def _digest_chunk(raw_text: str, provider: LLMProvider) -> tuple[DiaryDigest, bool]:
    prompt = load_prompt("field_diary").render(raw_text=raw_text)
    try:
        return structured_call(
            provider, prompt_name="field_diary", system="你只输出符合要求的 JSON 日记，不编造事实。",
            messages=[{"role": "user", "content": prompt}], model_cls=DiaryDigest,
            fallback=lambda: _fallback(raw_text), max_retries=1, temperature=0.2, max_tokens=1100,
        )
    except RuntimeError as exc:
        log.warning("前线日记整理暂不可用，保留原话：%s", exc)
        return _fallback(raw_text), True


def _digest(raw_text: str, provider: LLMProvider) -> tuple[DiaryDigest, bool]:
    if provider.name == "mock" and not provider.responses:
        return _fallback(raw_text), True
    parts = [_digest_chunk(chunk, provider) for chunk in _diary_chunks(raw_text)]
    if len(parts) == 1:
        return parts[0]
    return _merge_digests([part for part, _ in parts]), any(degraded for _, degraded in parts)


@router.post("", response_model=FieldDiary)
def create_diary(body: NewDiary, repo: Repo = Depends(get_repo), account: Account = Depends(get_current_account),
                 provider: LLMProvider = Depends(get_provider)):
    digest, degraded = _digest(body.raw_text, provider)
    item = FieldDiary(id=f"diary_{uuid4().hex}", owner_id=account.id, created_at=datetime.now(UTC),
                      hospital=body.hospital or _grounded_context(digest.hospital, body.raw_text),
                      doctor_name=body.doctor_name or _grounded_context(digest.doctor_name, body.raw_text),
                      raw_text=body.raw_text, digest=digest, degraded=degraded)
    repo.save(item)
    return item


@router.post("/preview", response_model=DiaryPreview)
def preview_diary(body: NewDiary, request: Request, account: Account = Depends(get_current_account),
                  provider: LLMProvider = Depends(get_provider)):
    if is_guest_account(account) and len(body.raw_text) > 4000:
        raise HTTPException(status_code=422, detail={"error": {"code": "preview_too_long",
                                                       "message": "试用预览最多 4000 字；创建账号后可保存更长口述"}})
    _rate_limit(request, "diary_preview", account.id, 3, 3600)
    digest, degraded = _digest(body.raw_text, provider)
    return DiaryPreview(raw_text=body.raw_text, digest=digest, degraded=degraded,
                        doctor_name=_grounded_context(digest.doctor_name, body.raw_text),
                        hospital=_grounded_context(digest.hospital, body.raw_text))


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
    if (not review or review.owner_id != account.id or review.policy_version != REVIEW_POLICY_VERSION
            or datetime.now(UTC) - review.reviewed_at >= timedelta(hours=24)):
        raise _not_found()
    return review


@router.post("/{diary_id}/review", response_model=DiaryReview)
def review_diary(diary_id: str, request: Request, refresh: bool = False, repo: Repo = Depends(get_repo),
                 account: Account = Depends(get_current_account), provider: LLMProvider = Depends(get_provider)):
    item = _own_diary(repo, diary_id, account)
    key = f"review_{diary_id}"
    cached = repo.get(DiaryReview, key)
    if (cached and cached.owner_id == account.id and cached.policy_version == REVIEW_POLICY_VERSION
            and not refresh and datetime.now(UTC) - cached.reviewed_at < timedelta(hours=24)):
        return cached
    _rate_limit(request, "diary_review", account.id, 20, 3600)
    radar = repo.get(AcademicRadar, radar_id(account.id, item.doctor_name, item.hospital)) if (
        item.doctor_name and item.hospital) else None
    review = DiaryReview(id=key, diary_id=diary_id, owner_id=account.id, reviewed_at=datetime.now(UTC),
                         policy_version=REVIEW_POLICY_VERSION,
                         findings=[assess_claim(claim, provider, raw_text=item.raw_text)
                                   for claim in extract_claims(item)],
                         academic_candidate_count=len(radar.works) if radar else 0)
    repo.save(review)
    item.review_status = "reviewed"
    repo.save(item)
    return review


@router.get("/{diary_id}/academic-crosscheck", response_model=AcademicCrosscheck)
def get_academic_crosscheck(diary_id: str, repo: Repo = Depends(get_repo),
                            account: Account = Depends(get_current_account)):
    item = _own_diary(repo, diary_id, account)
    cached = _valid_academic_cache(repo, item, account)
    if not cached:
        raise _not_found()
    return cached


@router.post("/{diary_id}/academic-crosscheck", response_model=AcademicCrosscheck)
def run_academic_crosscheck(diary_id: str, request: Request, repo: Repo = Depends(get_repo),
                            account: Account = Depends(get_current_account),
                            provider: LLMProvider = Depends(get_provider)):
    item = _own_diary(repo, diary_id, account)
    cached = _valid_academic_cache(repo, item, account)
    if cached:
        return cached
    _rate_limit(request, "academic_crosscheck", account.id, 20, 3600)
    result = compare_academic(item, _matching_radar(repo, item, account), provider)
    repo.save(result)
    return result


@router.delete("/{diary_id}")
def delete_diary(diary_id: str, repo: Repo = Depends(get_repo), account: Account = Depends(get_current_account)):
    _own_diary(repo, diary_id, account)
    repo.delete(DiaryReview, f"review_{diary_id}")
    repo.delete(AcademicCrosscheck, f"academic_{diary_id}")
    repo.delete(FieldDiary, diary_id)
    return {"ok": True}
