from __future__ import annotations

from datetime import datetime
from typing import Literal

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


class ReviewEvidence(BaseModel):
    id: str
    excerpt: str
    source: str
    url: str


class ClaimFinding(BaseModel):
    claim: str
    status: Literal["possible_conflict", "possible_support", "insufficient", "out_of_scope"]
    grounded_in_raw: bool = True
    note: str = ""
    evidence_id: str = ""
    evidence_quote: str = ""
    candidates: list[ReviewEvidence] = Field(default_factory=list, max_length=3)


class DiaryReview(BaseModel):
    id: str
    diary_id: str
    owner_id: str
    reviewed_at: datetime
    policy_version: str = ""
    findings: list[ClaimFinding] = Field(default_factory=list, max_length=6)
    academic_candidate_count: int = 0
    academic_identity_confirmed: bool = False
