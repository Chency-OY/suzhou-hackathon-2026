from __future__ import annotations

import re
from time import time

from pydantic import BaseModel, field_validator
from pydantic import Field as PydanticField
from sqlmodel import Field, SQLModel


class Account(SQLModel, table=True):
    id: str = Field(primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    created_at: int = Field(default_factory=lambda: int(time()))


class LoginSession(SQLModel, table=True):
    token_hash: str = Field(primary_key=True)
    account_id: str = Field(index=True)
    expires_at: int


class Credentials(BaseModel):
    username: str = PydanticField(min_length=3, max_length=24)
    password: str = PydanticField(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_format(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[a-z0-9_]{3,24}", normalized):
            raise ValueError("账号只能使用 3–24 位英文字母、数字和下划线")
        return normalized


class AccountPublic(BaseModel):
    id: str
    username: str


class SessionSummary(BaseModel):
    id: str
    scenario_id: str
    started_at: str
    ended_at: str | None
    end_reason: str | None
    rep_turns: int
