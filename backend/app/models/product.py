from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class ProductPortfolioItem(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    generic_name: str = Field(min_length=1)
    stage: Literal["marketed", "nda_review", "pivotal"]
    note: str
    target: str = Field(min_length=1)
    modality: str = Field(min_length=1)
    area: str = Field(min_length=1)
    overview: str = Field(min_length=20)
    overview_source_url: str = Field(pattern=r"^https://")
    key_points: list[str] = Field(default_factory=list, max_length=5)
    detail_source_url: str | None = Field(default=None, pattern=r"^https://")
    source_url: str = Field(pattern=r"^https://")
    checked_on: date
    verified: bool
