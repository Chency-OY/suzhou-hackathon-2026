from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DiaryDigest(BaseModel):
    summary: str = Field(min_length=1, max_length=500)
    first_impressions: list[str] = Field(default_factory=list, max_length=6)
    doctor_feedback: list[str] = Field(default_factory=list, max_length=6)
    what_to_improve: list[str] = Field(default_factory=list, max_length=6)
    next_visit: list[str] = Field(default_factory=list, max_length=6)
    uncertain_claims: list[str] = Field(default_factory=list, max_length=6)


class FieldDiary(BaseModel):
    id: str
    owner_id: str
    created_at: datetime
    hospital: str = ""
    doctor_name: str = ""
    raw_text: str
    digest: DiaryDigest
    degraded: bool = False
    review_status: str = "unreviewed"
