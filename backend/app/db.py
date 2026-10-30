from __future__ import annotations

from datetime import UTC, datetime
from typing import TypeVar

from pydantic import BaseModel
from sqlmodel import Field, SQLModel, create_engine, select
from sqlmodel import Session as DBSession

from .config import settings
from .models.auth import Account, LoginSession  # noqa: F401 - register auth tables in SQLModel metadata

M = TypeVar("M", bound=BaseModel)


class Record(SQLModel, table=True):
    kind: str = Field(primary_key=True)
    id: str = Field(primary_key=True)
    data: str
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Repo:
    def __init__(self, url: str | None = None):
        self.engine = create_engine(url or settings.db_url, connect_args={"check_same_thread": False})
        SQLModel.metadata.create_all(self.engine)

    def save(self, obj: BaseModel) -> None:
        with DBSession(self.engine) as s:
            s.merge(Record(kind=type(obj).__name__, id=obj.id, data=obj.model_dump_json()))  # type: ignore[attr-defined]
            s.commit()

    def get(self, cls: type[M], id: str) -> M | None:
        with DBSession(self.engine) as s:
            rec = s.get(Record, (cls.__name__, id))
            return cls.model_validate_json(rec.data) if rec else None

    def list(self, cls: type[M], limit: int | None = None) -> list[M]:
        with DBSession(self.engine) as s:
            stmt = select(Record).where(Record.kind == cls.__name__).order_by(Record.id)
            if limit:
                stmt = stmt.limit(limit)
            return [cls.model_validate_json(r.data) for r in s.exec(stmt).all()]

    def delete(self, cls: type[BaseModel], id: str) -> bool:
        with DBSession(self.engine) as s:
            rec = s.get(Record, (cls.__name__, id))
            if not rec:
                return False
            s.delete(rec)
            s.commit()
            return True
