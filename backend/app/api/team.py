from __future__ import annotations

import hashlib
import hmac
import secrets
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from ..db import Repo
from ..deps import get_repo
from ..models import Report, Session
from ..models.auth import Account
from ..models.constants import SIGNALS
from ..models.team import Team, TeamInfo, TeamInsights, TeamMembership
from .auth import _rate_limit, get_current_account

router = APIRouter(prefix="/api/team")


def _error(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"error": {"code": code, "message": message}})


def _owned_team(repo: Repo, account: Account) -> tuple[Team, TeamMembership]:
    member = repo.get(TeamMembership, account.id)
    team = repo.get(Team, member.team_id) if member else None
    if not team:
        raise _error(404, "no_team", "尚未加入团队")
    return team, member


def _info(repo: Repo, team: Team, member: TeamMembership, code: str = "") -> TeamInfo:
    size = sum(item.team_id == team.id for item in repo.list(TeamMembership))
    return TeamInfo(id=team.id, name=team.name, role=member.role, member_count=size, invite_code=code)


class NewTeam(BaseModel):
    name: str = Field(min_length=2, max_length=60)

    @field_validator("name")
    @classmethod
    def trim(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("团队名称至少需要两个字")
        return value


class JoinTeam(BaseModel):
    invite_code: str = Field(min_length=12, max_length=64)


@router.post("", response_model=TeamInfo)
def create_team(body: NewTeam, request: Request, repo: Repo = Depends(get_repo),
                account: Account = Depends(get_current_account)):
    if repo.get(TeamMembership, account.id):
        raise _error(409, "already_in_team", "请先退出当前团队")
    _rate_limit(request, "team_create", account.id, 3, 3600)
    code = secrets.token_urlsafe(18)
    team = Team(id=f"team_{uuid4().hex}", name=body.name, owner_id=account.id,
                invite_hash=hashlib.sha256(code.encode()).hexdigest())
    member = TeamMembership(id=account.id, team_id=team.id, account_id=account.id, role="owner")
    repo.save(team)
    repo.save(member)
    return _info(repo, team, member, code)


@router.get("", response_model=TeamInfo)
def get_team(repo: Repo = Depends(get_repo), account: Account = Depends(get_current_account)):
    team, member = _owned_team(repo, account)
    return _info(repo, team, member)


@router.post("/join", response_model=TeamInfo)
def join_team(body: JoinTeam, request: Request, repo: Repo = Depends(get_repo),
              account: Account = Depends(get_current_account)):
    if repo.get(TeamMembership, account.id):
        raise _error(409, "already_in_team", "请先退出当前团队")
    _rate_limit(request, "team_join", account.id, 8, 3600)
    digest = hashlib.sha256(body.invite_code.strip().encode()).hexdigest()
    team = next((item for item in repo.list(Team) if hmac.compare_digest(item.invite_hash, digest)), None)
    if not team:
        raise _error(404, "invalid_invite", "邀请码无效")
    member = TeamMembership(id=account.id, team_id=team.id, account_id=account.id, role="member")
    repo.save(member)
    return _info(repo, team, member)


@router.post("/invite", response_model=TeamInfo)
def rotate_invite(request: Request, repo: Repo = Depends(get_repo),
                  account: Account = Depends(get_current_account)):
    team, member = _owned_team(repo, account)
    if member.role != "owner":
        raise _error(403, "owner_only", "只有创建者可以生成邀请码")
    _rate_limit(request, "team_invite", account.id, 5, 3600)
    code = secrets.token_urlsafe(18)
    team.invite_hash = hashlib.sha256(code.encode()).hexdigest()
    repo.save(team)
    return _info(repo, team, member, code)


@router.post("/leave")
def leave_team(repo: Repo = Depends(get_repo), account: Account = Depends(get_current_account)):
    _, member = _owned_team(repo, account)
    if member.role == "owner":
        raise _error(409, "owner_cannot_leave", "创建者暂不能退出团队")
    repo.delete(TeamMembership, account.id)
    return {"ok": True}


@router.get("/insights", response_model=TeamInsights)
def get_insights(repo: Repo = Depends(get_repo), account: Account = Depends(get_current_account)):
    team, _ = _owned_team(repo, account)
    ids = {member.account_id for member in repo.list(TeamMembership) if member.team_id == team.id}
    sessions = [item for item in repo.list(Session) if item.rep_id in ids and item.ended_at]
    counts = {signal: 0 for signal in SIGNALS}
    scores = []
    for session in sessions:
        seen = {signal for turn in session.turns if turn.speaker == "rep" for signal in turn.signals}
        for signal in seen:
            if signal in counts:
                counts[signal] += 1
        report = repo.get(Report, f"report_{session.id}")
        if report and report.scoring_mode == "model":
            scores.append(report.total_score)
    return TeamInsights(team_id=team.id, completed_sessions=len(sessions), scored_sessions=len(scores),
                        average_score=round(sum(scores) / len(scores), 1) if scores else None,
                        signal_counts=counts)
