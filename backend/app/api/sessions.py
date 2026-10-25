from __future__ import annotations

import threading
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from ..db import Repo
from ..deps import get_engine, get_repo
from ..models import DoctorPersona, DoctorState, Scenario, Session
from ..sessions import SessionEngine

router = APIRouter(prefix="/api")
_locks: dict[str, threading.Lock] = {}
_guard = threading.Lock()


def _lock(sid: str) -> threading.Lock:
    with _guard:
        return _locks.setdefault(sid, threading.Lock())


def _err(status: int, code: str, msg: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"error": {"code": code, "message": msg}})


class CreateSessionIn(BaseModel):
    scenario_id: str = Field(min_length=1, max_length=64)
    rep_id: str = Field(min_length=1, max_length=64)


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


class SessionOut(BaseModel):
    id: str
    scenario_id: str
    rep_id: str
    started_at: datetime
    ended_at: datetime | None
    end_reason: str | None
    turns: list[TurnView]


def _load(repo: Repo, session_id: str) -> tuple[Session, Scenario, DoctorPersona]:
    s = repo.get(Session, session_id)
    sc = repo.get(Scenario, s.scenario_id) if s else None
    p = repo.get(DoctorPersona, sc.persona_id) if sc else None
    if not (s and sc and p):
        raise _err(404, "not_found", "会话不存在")
    return s, sc, p


@router.post("/sessions", response_model=CreateSessionOut)
def create_session(body: CreateSessionIn, repo: Repo = Depends(get_repo),
                   engine: SessionEngine = Depends(get_engine)):
    sc = repo.get(Scenario, body.scenario_id)
    p = repo.get(DoctorPersona, sc.persona_id) if sc else None
    if not (sc and p):
        raise _err(404, "not_found", "场景不存在")
    session = engine.start(sc, p, body.rep_id)
    repo.save(session)
    return CreateSessionOut(session_id=session.id, opening_line=sc.opening_line,
                            doctor_state=session.turns[0].state_after)


@router.post("/sessions/{session_id}/turns", response_model=TurnOut)
def post_turn(session_id: str, body: TurnIn, repo: Repo = Depends(get_repo),
              engine: SessionEngine = Depends(get_engine)):
    with _lock(session_id):
        session, sc, p = _load(repo, session_id)
        if session.ended_at:
            raise _err(409, "session_ended", "演练已结束")
        res = engine.step(session, sc, p, body.text)
        repo.save(session)
    return TurnOut(doctor_reply=res.doctor_reply, doctor_state=res.state, signals=res.signals, ended=res.ended,
                   end_reason=res.end_reason, degraded=res.degraded)


@router.post("/sessions/{session_id}/finish", response_model=FinishOut)
def finish_session(session_id: str, repo: Repo = Depends(get_repo)):
    with _lock(session_id):
        session, _, _ = _load(repo, session_id)
        if not session.ended_at:
            session.ended_at = datetime.now(UTC)
            session.end_reason = "rep_ended"
            repo.save(session)
    return FinishOut(session_id=session.id, ended=True, end_reason=session.end_reason, report_id=None)


@router.get("/sessions/{session_id}", response_model=SessionOut)
def get_session(session_id: str, repo: Repo = Depends(get_repo)):
    s, _, _ = _load(repo, session_id)
    return SessionOut(
        id=s.id, scenario_id=s.scenario_id, rep_id=s.rep_id, started_at=s.started_at, ended_at=s.ended_at,
        end_reason=s.end_reason,
        turns=[TurnView(idx=t.idx, speaker=t.speaker, text=t.text, signals=list(t.signals),
                        state_after=t.state_after) for t in s.turns])
