from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from ..db import Repo
from ..deps import get_provider, get_repo
from ..llm import LLMProvider
from ..models.auth import Account
from ..models.radar import AcademicRadar, AutoRefreshChoice
from ..radar.deepseek_web import search_web, synthesize_answer
from ..radar.openalex import radar_id, search_academic
from .auth import _rate_limit, get_current_account

router = APIRouter(prefix="/api/radar")
log = logging.getLogger(__name__)
RADAR_VERSION = "deepseek-web-v2-auto"


class RadarSearch(BaseModel):
    doctor_name: str = Field(min_length=2, max_length=80)
    hospital: str = Field(min_length=4, max_length=120)
    refresh: bool = False
    auto_refresh: bool | None = None

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


@router.patch("/{radar_id}/auto-refresh", response_model=AcademicRadar)
def set_auto_refresh(radar_id: str, body: AutoRefreshChoice, repo: Repo = Depends(get_repo),
                     account: Account = Depends(get_current_account)):
    item = repo.get(AcademicRadar, radar_id)
    if not item or item.owner_id != account.id:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "雷达记录不存在"}})
    item.auto_refresh = body.enabled
    item.refresh_error = ""
    repo.save(item)
    return item


def collect_radar(repo: Repo, owner_id: str, doctor_name: str, hospital: str,
                  provider: LLMProvider, cached: AcademicRadar | None = None) -> AcademicRadar:
    key = radar_id(owner_id, doctor_name, hospital)
    if cached is None:
        cached = repo.get(AcademicRadar, key)
    web_sources = []
    evidence = {}
    web_status = "unavailable"
    try:
        web_sources, evidence, web_status = search_web(doctor_name, hospital)
    except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
        log.warning("DeepSeek 实时网页检索暂不可用：%s", type(exc).__name__)
    if cached and web_status != "ok":
        return cached
    answer_points = synthesize_answer(doctor_name, hospital, web_sources, evidence, provider)
    try:
        result = search_academic(owner_id, doctor_name, hospital)
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        log.warning("OpenAlex 论文索引暂不可用：%s", type(exc).__name__)
        if cached and not web_sources:
            return cached
        result = AcademicRadar(id=key, owner_id=owner_id, doctor_name=doctor_name,
                               hospital=hospital, searched_at=datetime.now(UTC), status="no_match")
    if web_status == "unavailable" and not result.works:
        if cached:
            return cached
        raise HTTPException(status_code=503, detail={"error": {"code": "radar_unavailable",
                                                       "message": "实时检索暂不可用，请稍后重试"}})
    result.web_sources = web_sources
    result.answer_points = answer_points
    result.web_status = web_status
    result.radar_version = RADAR_VERSION
    result.auto_refresh = cached.auto_refresh if cached else False
    result.last_auto_checked_at = cached.last_auto_checked_at if cached else None
    result.refresh_error = "" if web_status == "ok" else "网页检索暂不可用；已保留可核对的论文索引。"
    if web_sources:
        result.status = "found"
    notes = ["DeepSeek 实时检索公开网页，OpenAlex 补充论文候选；搜索结果不保证完整。"]
    if web_status != "ok":
        notes.append("实时网页检索暂不可用，当前主要显示论文索引候选。")
    elif not web_sources:
        notes.append("本次网页检索未返回可展示来源，不能据此判断没有相关资料。")
    elif not answer_points:
        notes.append("没有足够的姓名、医院和原文依据生成回答，请逐条核对候选链接。")
    notes.append("同名作者或演讲者身份未确认；网页和论文候选都不能直接写入医生画像。")
    result.note = "".join(notes)
    repo.save(result)
    return result


@router.post("/search", response_model=AcademicRadar)
def run_radar(body: RadarSearch, request: Request, repo: Repo = Depends(get_repo),
              account: Account = Depends(get_current_account), provider: LLMProvider = Depends(get_provider)):
    key = radar_id(account.id, body.doctor_name, body.hospital)
    cached = repo.get(AcademicRadar, key)
    if (cached and cached.radar_version == RADAR_VERSION and cached.web_status != "unavailable"
            and not body.refresh and datetime.now(UTC) - cached.searched_at < timedelta(hours=24)):
        if body.auto_refresh is not None and cached.auto_refresh != body.auto_refresh:
            cached.auto_refresh = body.auto_refresh
            repo.save(cached)
        return cached
    _rate_limit(request, "radar", account.id, 20, 3600)
    result = collect_radar(repo, account.id, body.doctor_name, body.hospital, provider, cached)
    if body.auto_refresh is not None and result.auto_refresh != body.auto_refresh:
        result.auto_refresh = body.auto_refresh
        repo.save(result)
    return result


@router.post("/refresh-due", response_model=list[AcademicRadar])
def refresh_due(request: Request, repo: Repo = Depends(get_repo),
                account: Account = Depends(get_current_account), provider: LLMProvider = Depends(get_provider)):
    from ..radar.auto_refresh import refresh_due_radars

    _rate_limit(request, "radar_refresh_due", account.id, 3, 3600)
    return refresh_due_radars(repo, account.id, provider)
