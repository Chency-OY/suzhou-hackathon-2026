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
    note: str = ""
