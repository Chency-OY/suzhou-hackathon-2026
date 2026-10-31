from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class Team(BaseModel):
    id: str
    name: str = Field(min_length=2, max_length=60)
    owner_id: str
    invite_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TeamMembership(BaseModel):
    id: str  # 与 account_id 相同，确保一个账号只有一个团队
    team_id: str
    account_id: str
    role: Literal["owner", "member"]


class TeamInfo(BaseModel):
    id: str
    name: str
    role: Literal["owner", "member"]
    member_count: int
    invite_code: str = ""


class TeamInsights(BaseModel):
    team_id: str
    completed_sessions: int
    scored_sessions: int
    average_score: float | None = None
    signal_counts: dict[str, int]
