from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from ..db import Repo
from ..deps import get_repo
from ..models.auth import Account
from ..models.radar import AcademicRadar
from ..radar.openalex import radar_id, search_academic
from .auth import _rate_limit, get_current_account

router = APIRouter(prefix="/api/radar")
log = logging.getLogger(__name__)


class RadarSearch(BaseModel):
    doctor_name: str = Field(min_length=2, max_length=80)
    hospital: str = Field(min_length=4, max_length=120)
    refresh: bool = False

    @field_validator("doctor_name", "hospital")
    @classmethod
    def trim(cls, value: str, info) -> str:
        value = value.strip()
        minimum = 2 if info.field_name == "doctor_name" else 4
        if len(value) < minimum:
            raise ValueError("请输入完整的姓名和医院")
        return value


@router.get("", response_model=list[AcademicRadar])
def list_radar(repo: Repo = Depends(get_repo), account: Account = Depends(get_current_account)):
    own = (item for item in repo.list(AcademicRadar) if item.owner_id == account.id)
    return sorted(own, key=lambda item: item.searched_at, reverse=True)[:30]


@router.post("/search", response_model=AcademicRadar)
def run_radar(body: RadarSearch, request: Request, repo: Repo = Depends(get_repo),
              account: Account = Depends(get_current_account)):
    key = radar_id(account.id, body.doctor_name, body.hospital)
    cached = repo.get(AcademicRadar, key)
    if cached and not body.refresh and datetime.now(UTC) - cached.searched_at < timedelta(hours=24):
        return cached
    _rate_limit(request, "radar", account.id, 20, 3600)
    try:
        result = search_academic(account.id, body.doctor_name, body.hospital)
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        log.warning("公开学术索引暂不可用：%s", exc)
        if cached:
            return cached
        raise HTTPException(status_code=503, detail={"error": {"code": "radar_unavailable",
                                                       "message": "公开学术索引暂不可用，请稍后重试"}}) from exc
    repo.save(result)
    return result
