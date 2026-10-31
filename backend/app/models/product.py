from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class ProductPortfolioItem(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    generic_name: str = Field(min_length=1)
    stage: Literal["marketed", "nda_review", "pivotal"]
    note: str
    source_url: str = Field(pattern=r"^https://")
    checked_on: date
    verified: bool
