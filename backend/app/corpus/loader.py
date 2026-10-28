from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

BANK_PATH = Path("data/corpus/scene_bank_v1.yaml")
_PCT = re.compile(r"\d+(?:\.\d+)?\s*%")


class Skeleton(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    title: str
    src: list[str] = Field(default_factory=list)
    setting: dict[str, Any] = Field(default_factory=dict)
    rep_pre_info: str
    rep_goal: str
    doctor: dict[str, Any] = Field(default_factory=dict)
    opening_lines: list[str] = Field(min_length=1)
    turn_plan: list[str] = Field(default_factory=list)
    gold_moves: list[str] = Field(default_factory=list)
    compliance_checks: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(min_length=1)
    events: list[str] = Field(default_factory=list)
    hard_gate: bool = False
    post_task: str | None = None


class SceneBank(BaseModel):
    model_config = ConfigDict(extra="ignore")

    meta: dict[str, Any] = Field(default_factory=dict)
    utterance_bank: dict[str, list[Any]] = Field(default_factory=dict)
    environment_events: list[str] = Field(default_factory=list)
    scene_skeletons: list[Skeleton]
    scoring_alignment: dict[str, Any] = Field(default_factory=dict)

    def lines(self, category: str) -> list[str]:
        out: list[str] = []
        for it in self.utterance_bank.get(category, []):
            out.append(str(it["text"]) if isinstance(it, dict) else str(it))
        return out

    def closing(self, kind: str) -> list[str]:
        return [str(it["text"]) for it in self.utterance_bank.get("closing_lines", [])
                if isinstance(it, dict) and it.get("kind") == kind]

    def skeleton(self, sid: str) -> Skeleton:
        return next(s for s in self.scene_skeletons if s.id == sid)


@lru_cache
def _load(path: str) -> SceneBank:
    return SceneBank(**yaml.safe_load(Path(path).read_text(encoding="utf-8")))


def load_bank(path: str | Path = BANK_PATH) -> SceneBank:
    return _load(str(path))


def validate_bank(bank: SceneBank) -> list[str]:
    errs: list[str] = []
    ids = [s.id for s in bank.scene_skeletons]
    if len(ids) != len(set(ids)):
        errs.append("骨架 id 重复")
    for s in bank.scene_skeletons:
        blob = " ".join([s.title, s.rep_pre_info, s.rep_goal, *s.opening_lines, *s.turn_plan, *s.gold_moves,
                         *s.compliance_checks, *s.success_criteria])
        if _PCT.search(blob):
            errs.append(f"{s.id} 含百分比数据")
        if not s.compliance_checks:
            errs.append(f"{s.id} 缺少合规检查点")
        for o in s.opening_lines:
            if not 4 <= len(o) <= 60:
                errs.append(f"{s.id} 开场白长度应为 4~60 字：{o}")
    for cat in bank.utterance_bank:
        for text in bank.lines(cat):
            if _PCT.search(text):
                errs.append(f"台词库 {cat} 含百分比数据：{text}")
    return errs
