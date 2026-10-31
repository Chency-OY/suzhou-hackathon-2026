from __future__ import annotations

import hashlib
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..db import Repo
from ..deps import get_provider, get_repo
from ..llm import LLMProvider
from ..models import DoctorPersona, PlaybookCard, Report, Scenario, Session
from ..models.auth import Account
from ..models.team import PlaybookCardView
from ..playbook import card_is_safe, extract_card
from .auth import _rate_limit, get_current_account
from .team import _owned_team

router = APIRouter(prefix="/api/playbook-cards")


def _error(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"error": {"code": code, "message": message}})


def _view(card: PlaybookCard) -> PlaybookCardView:
    return PlaybookCardView(id=card.id, title=card.title, situation=card.situation,
                            effective_response_pattern=card.effective_response_pattern,
                            example_lines=card.example_lines,
                            status=card.status, scenario_id=f"scn_{card.id}" if card.status == "approved" else "")


class ExtractIn(BaseModel):
    session_id: str = Field(min_length=1, max_length=80)


@router.get("", response_model=list[PlaybookCardView])
def list_cards(status: Literal["candidate", "approved", "rejected"] | None = None,
               repo: Repo = Depends(get_repo), account: Account = Depends(get_current_account)):
    team, member = _owned_team(repo, account)
    cards = (card for card in repo.list(PlaybookCard) if card.team_id == team.id and
             (member.role == "owner" or card.status == "approved" or card.created_by == account.id) and
             (status is None or card.status == status))
    return [_view(card) for card in cards]


@router.post("/extract", response_model=PlaybookCardView)
def extract(body: ExtractIn, request: Request, repo: Repo = Depends(get_repo),
            account: Account = Depends(get_current_account), provider: LLMProvider = Depends(get_provider)):
    team, _ = _owned_team(repo, account)
    session = repo.get(Session, body.session_id)
    if not session or session.rep_id != account.id:
        raise _error(404, "not_found", "演练不存在")
    report = repo.get(Report, f"report_{session.id}")
    if not (session.ended_at and report and report.scoring_mode == "model"
            and report.total_score >= 80 and not report.capped_by_compliance):
        raise _error(422, "not_eligible", "仅可从本人已完成、80 分及以上且无红线的演练提炼")
    card_id = "card_" + hashlib.sha256(f"{team.id}:{session.id}".encode()).hexdigest()[:20]
    existing = repo.get(PlaybookCard, card_id)
    if existing:
        return _view(existing)
    _rate_limit(request, "playbook_extract", account.id, 10, 3600)
    scenario = repo.get(Scenario, session.scenario_id)
    persona = repo.get(DoctorPersona, scenario.persona_id) if scenario else None
    if not scenario or not persona or (scenario.team_id and scenario.team_id != team.id):
        raise _error(404, "not_found", "训练场景不存在")
    card = extract_card(session, scenario, persona, provider, card_id, team.id, account.id, report.total_score)
    if not card:
        raise _error(503, "extract_unavailable", "暂无法安全提炼打法卡片，请稍后重试")
    repo.save(card)
    return _view(card)


@router.post("/{card_id}/approve", response_model=PlaybookCardView)
def approve(card_id: str, repo: Repo = Depends(get_repo), account: Account = Depends(get_current_account)):
    team, member = _owned_team(repo, account)
    if member.role != "owner":
        raise _error(403, "owner_only", "只有团队创建者可以审核打法卡片")
    card = repo.get(PlaybookCard, card_id)
    if not card or card.team_id != team.id:
        raise _error(404, "not_found", "卡片不存在")
    if card.status == "rejected":
        raise _error(409, "card_rejected", "已拒绝的卡片不能批准")
    if not card_is_safe(card):
        raise _error(422, "unsafe_card", "卡片内容需要重新核对")
    original = repo.get(Scenario, card.source_scenario_id)
    if not original or (original.team_id and original.team_id != team.id):
        raise _error(404, "not_found", "原训练场景不存在")
    scenario_id = f"scn_{card.id}"
    if not repo.get(Scenario, scenario_id):
        scenario = original.model_copy(update={
            "id": scenario_id, "team_id": team.id, "source": "playbook",
            "rep_goal": f"练习：{card.effective_response_pattern}",
            "context_brief": f"{original.context_brief} 本次重点：{card.situation}",
            "success_criteria": [card.effective_response_pattern],
        })
        repo.save(scenario)
    card.status = "approved"
    repo.save(card)
    return _view(card)


@router.post("/{card_id}/reject", response_model=PlaybookCardView)
def reject(card_id: str, repo: Repo = Depends(get_repo), account: Account = Depends(get_current_account)):
    team, member = _owned_team(repo, account)
    if member.role != "owner":
        raise _error(403, "owner_only", "只有团队创建者可以审核打法卡片")
    card = repo.get(PlaybookCard, card_id)
    if not card or card.team_id != team.id:
        raise _error(404, "not_found", "卡片不存在")
    if card.status == "approved":
        raise _error(409, "already_approved", "已批准的卡片不能拒绝")
    card.status = "rejected"
    repo.save(card)
    return _view(card)
