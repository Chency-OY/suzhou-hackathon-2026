from __future__ import annotations

import threading
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from ..db import Repo
from ..deps import get_engine, get_provider, get_repo
from ..diary_rehearsal import rehearsal_mood, rehearsal_note
from ..llm import LLMProvider
from ..models import DoctorPersona, DoctorState, Report, Scenario, Session
from ..models.auth import Account, SessionSummary
from ..models.diary import FieldDiary
from ..scoring import score_session
from ..sessions import SessionEngine
from .auth import get_current_account, is_guest_account

router = APIRouter(prefix="/api")
_locks: dict[str, threading.Lock] = {}
_guard = threading.Lock()
GUEST_MAX_SESSIONS = 2
GUEST_MAX_TURNS = 6


def _lock(sid: str) -> threading.Lock:
    with _guard:
        return _locks.setdefault(sid, threading.Lock())


def _err(status: int, code: str, msg: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"error": {"code": code, "message": msg}})


class CreateSessionIn(BaseModel):
    scenario_id: str = Field(min_length=1, max_length=64)
    diary_id: str | None = Field(default=None, max_length=80)


class CreateSessionOut(BaseModel):
    session_id: str
    opening_line: str
    doctor_state: DoctorState


class TurnIn(BaseModel):
    text: str = Field(max_length=2000)

    @field_validator("text")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("内容不能为空")
        return v


class TurnOut(BaseModel):
    doctor_reply: str
    doctor_state: DoctorState
    signals: list[str]
    ended: bool
    end_reason: str | None
    degraded: bool
    judge_note: str = ""
    judge_degraded: bool = False
    report_id: str | None = None


class FinishOut(BaseModel):
    session_id: str
    ended: bool
    end_reason: str | None
    report_id: str | None = None      # Day 4 评分上线后填充


class TurnView(BaseModel):
    idx: int
    speaker: str
    text: str
    signals: list[str]
    state_after: DoctorState | None
    judge_note: str = ""
    judge_degraded: bool = False


class SessionOut(BaseModel):
    id: str
    scenario_id: str
    rep_id: str
    started_at: datetime
    ended_at: datetime | None
    end_reason: str | None
    diary_id: str | None = None
    rehearsal_note: str = ""
    rehearsal_mood: str = ""
    turns: list[TurnView]


class ReportOut(Report):
    turns: list[TurnView]


def _turn_views(session: Session) -> list[TurnView]:
    return [TurnView(idx=t.idx, speaker=t.speaker, text=t.text, signals=list(t.signals),
                     state_after=t.state_after,
                     judge_note=str(t.meta.get("judge_note", "")) if t.speaker == "rep" else "",
                     judge_degraded=bool(t.meta.get("judge_degraded", False)) if t.speaker == "rep" else False)
            for t in session.turns]


def _ensure_report(repo: Repo, session: Session, scenario: Scenario, provider: LLMProvider) -> Report:
    key = f"report_{session.id}"
    existing = repo.get(Report, key)
    if existing:
        return existing
    report = score_session(session, scenario, provider)
    repo.save(report)
    return report


def _own_rehearsal(repo: Repo, diary_id: str | None, account: Account, allow_missing: bool = False) -> str:
    if not diary_id:
        return ""
    diary = repo.get(FieldDiary, diary_id)
    if not diary or diary.owner_id != account.id:
        if allow_missing:
            return ""
        raise _err(404, "not_found", "日记不存在")
    return rehearsal_note(diary)


def _load(repo: Repo, session_id: str, account: Account) -> tuple[Session, Scenario, DoctorPersona]:
    s = repo.get(Session, session_id)
    if s and s.rep_id != account.id:
        raise _err(404, "not_found", "会话不存在")
    sc = repo.get(Scenario, s.scenario_id) if s else None
    p = repo.get(DoctorPersona, sc.persona_id) if sc else None
    if not (s and sc and p):
        raise _err(404, "not_found", "会话不存在")
    return s, sc, p


@router.get("/sessions", response_model=list[SessionSummary])
def list_sessions(repo: Repo = Depends(get_repo), account: Account = Depends(get_current_account)):
    sessions = sorted((item for item in repo.list(Session) if item.rep_id == account.id),
                      key=lambda item: item.started_at, reverse=True)[:100]
    return [SessionSummary(id=item.id, scenario_id=item.scenario_id,
                           started_at=item.started_at.isoformat(),
                           ended_at=item.ended_at.isoformat() if item.ended_at else None,
                           end_reason=item.end_reason,
                           rep_turns=sum(turn.speaker == "rep" for turn in item.turns)) for item in sessions]


@router.post("/sessions", response_model=CreateSessionOut)
def create_session(body: CreateSessionIn, repo: Repo = Depends(get_repo),
                   account: Account = Depends(get_current_account),
                   engine: SessionEngine = Depends(get_engine)):
    sc = repo.get(Scenario, body.scenario_id)
    p = repo.get(DoctorPersona, sc.persona_id) if sc else None
    if not (sc and p):
        raise _err(404, "not_found", "场景不存在")
    if sc.team_id:
        raise _err(404, "not_found", "场景不存在")
    if is_guest_account(account) and body.diary_id:
        raise _err(403, "guest_limited", "试用模式不能使用私人日记")
    if body.diary_id and not _own_rehearsal(repo, body.diary_id, account):
        raise _err(422, "no_rehearsal_cues", "这篇日记没有可用于沟通练习的观察")
    with _lock(f"account:{account.id}"):
        if is_guest_account(account) and sum(item.rep_id == account.id for item in repo.list(Session)) >= GUEST_MAX_SESSIONS:
            raise _err(429, "guest_limit", "试用次数已用完；创建账号可继续练习并保留已有记录")
        session = engine.start(sc, p, account.id, diary_id=body.diary_id)
        repo.save(session)
    return CreateSessionOut(session_id=session.id, opening_line=sc.opening_line,
                            doctor_state=session.turns[0].state_after)


@router.post("/sessions/{session_id}/turns", response_model=TurnOut)
def post_turn(session_id: str, body: TurnIn, repo: Repo = Depends(get_repo),
              account: Account = Depends(get_current_account),
              engine: SessionEngine = Depends(get_engine), provider: LLMProvider = Depends(get_provider)):
    with _lock(session_id):
        session, sc, p = _load(repo, session_id, account)
        if session.ended_at:
            raise _err(409, "session_ended", "演练已结束")
        if is_guest_account(account) and sum(turn.speaker == "rep" for turn in session.turns) >= GUEST_MAX_TURNS:
            raise _err(429, "guest_limit", "本次试用回答已达上限；创建账号可继续练习并保留记录")
        note = _own_rehearsal(repo, session.diary_id, account, allow_missing=True)
        res = engine.step(session, sc, p, body.text, rehearsal_note=note)
        repo.save(session)
        report_id = _ensure_report(repo, session, sc, provider).id if session.ended_at else None
    return TurnOut(doctor_reply=res.doctor_reply, doctor_state=res.state, signals=res.signals, ended=res.ended,
                   end_reason=res.end_reason, degraded=res.degraded, report_id=report_id,
                   judge_note=res.judge_note, judge_degraded=res.judge_degraded)


@router.post("/sessions/{session_id}/finish", response_model=FinishOut)
def finish_session(session_id: str, repo: Repo = Depends(get_repo),
                   account: Account = Depends(get_current_account), provider: LLMProvider = Depends(get_provider)):
    with _lock(session_id):
        session, scenario, _ = _load(repo, session_id, account)
        if not session.ended_at:
            session.ended_at = datetime.now(UTC)
            session.end_reason = "rep_ended"
            repo.save(session)
        report_id = _ensure_report(repo, session, scenario, provider).id
    return FinishOut(session_id=session.id, ended=True, end_reason=session.end_reason, report_id=report_id)


@router.get("/sessions/{session_id}", response_model=SessionOut)
def get_session(session_id: str, repo: Repo = Depends(get_repo),
                account: Account = Depends(get_current_account)):
    s, _, _ = _load(repo, session_id, account)
    note = _own_rehearsal(repo, s.diary_id, account, allow_missing=True)
    return SessionOut(
        id=s.id, scenario_id=s.scenario_id, rep_id=s.rep_id, started_at=s.started_at, ended_at=s.ended_at,
        end_reason=s.end_reason, diary_id=s.diary_id, rehearsal_note=note,
        rehearsal_mood=rehearsal_mood(note) or "",
        turns=_turn_views(s))


@router.get("/reports/{report_id}", response_model=ReportOut)
def get_report(report_id: str, repo: Repo = Depends(get_repo),
               account: Account = Depends(get_current_account)):
    report = repo.get(Report, report_id)
    session = repo.get(Session, report.session_id) if report else None
    if not session or session.rep_id != account.id:
        raise _err(404, "not_found", "报告不存在")
    return ReportOut(**report.model_dump(), turns=_turn_views(session))
