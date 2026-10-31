from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AcademicWork(BaseModel):
    id: str
    title: str
    publication_date: str = ""
    journal: str = ""
    author_name: str
    affiliation: str
    url: str
    doi: str = ""
    identity_status: Literal["candidate", "confirmed"] = "candidate"


class RadarWebSource(BaseModel):
    id: str
    kind: Literal["paper", "conference", "talk"]
    title: str
    url: str
    site_name: str = ""
    published_at: str = ""
    snippet: str = ""
    name_in_source: bool = False
    hospital_in_source: bool = False
    identity_status: Literal["candidate"] = "candidate"


class RadarAnswerPoint(BaseModel):
    kind: Literal["paper", "conference", "talk"]
    statement: str = Field(min_length=1, max_length=240)
    source_id: str
    evidence_quote: str = Field(min_length=8, max_length=240)


class RadarAnswerDraft(BaseModel):
    points: list[RadarAnswerPoint] = Field(default_factory=list, max_length=8)


class AcademicRadar(BaseModel):
    id: str
    owner_id: str
    doctor_name: str
    hospital: str
    searched_at: datetime
    institution_name: str = ""
    institution_url: str = ""
    search_name: str = ""
    status: Literal["found", "no_match", "ambiguous_institution"]
    works: list[AcademicWork] = Field(default_factory=list, max_length=25)
    web_sources: list[RadarWebSource] = Field(default_factory=list, max_length=18)
    answer_points: list[RadarAnswerPoint] = Field(default_factory=list, max_length=8)
    web_status: Literal["ok", "unavailable", "not_configured"] = "not_configured"
    radar_version: str = ""
    note: str = ""
