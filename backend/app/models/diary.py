from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DiaryDigest(BaseModel):
    summary: str = Field(min_length=1, max_length=500)
    doctor_name: str = Field(default="", max_length=80)
    hospital: str = Field(default="", max_length=120)
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


class DiaryPreview(BaseModel):
    raw_text: str
    doctor_name: str = ""
    hospital: str = ""
    digest: DiaryDigest
    degraded: bool = False


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


class AcademicTensionDraft(BaseModel):
    diary_quote: str = Field(min_length=8, max_length=240)
    source_id: str
    source_quote: str = Field(min_length=8, max_length=240)


class AcademicCrossDraft(BaseModel):
    tensions: list[AcademicTensionDraft] = Field(default_factory=list, max_length=5)


class AcademicTension(BaseModel):
    diary_quote: str
    source_id: str
    source_quote: str
    source_title: str
    source_url: str
    note: str = "同名网页线索与日记原话可能有出入，需核对原网页及人物身份。"


class AcademicCrosscheck(BaseModel):
    id: str
    diary_id: str
    owner_id: str
    radar_id: str = ""
    checked_at: datetime
    policy_version: str
    status: Literal["compared", "insufficient", "no_radar"]
    tensions: list[AcademicTension] = Field(default_factory=list, max_length=5)
    note: str
