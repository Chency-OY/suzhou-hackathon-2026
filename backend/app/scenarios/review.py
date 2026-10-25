from __future__ import annotations

import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from ..models import DoctorPersona, Scenario
from .generate import TRAP_WORDS, _norm, leaks_hidden

REVIEW_PATH = Path("data/scenarios/review.json")
PRESCREEN_PATH = Path("data/scenarios/prescreen.json")
STATUSES = {"pending", "approved", "needs_fix", "rejected"}
COOPERATIVE = ["欢迎", "请讲", "没问题", "很高兴", "随时", "你说吧", "您说", "请坐", "太好了"]


def load_review(path: str | Path = REVIEW_PATH) -> dict[str, dict]:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() and p.read_text(encoding="utf-8").strip() else {}


def save_review(data: dict[str, dict], path: str | Path = REVIEW_PATH) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def set_status(data: dict[str, dict], sid: str, status: str, reason: str = "") -> None:
    if status not in STATUSES:
        raise ValueError(f"非法状态：{status}")
    data[sid] = {"status": status, "reason": reason, "at": datetime.now(UTC).isoformat(timespec="seconds")}


def status_of(data: dict[str, dict], sid: str) -> str:
    return data.get(sid, {}).get("status", "pending")


def rejected_ids(data: dict[str, dict]) -> set[str]:
    return {k for k, v in data.items() if v.get("status") == "rejected"}


def usable(scenarios: list[Scenario], data: dict[str, dict] | None = None) -> list[Scenario]:
    data = load_review() if data is None else data
    bad = rejected_ids(data)
    return [s for s in scenarios if s.id not in bad]


def heuristic_flags(p: DoctorPersona, s: Scenario, opening_counts: Counter) -> list[str]:
    flags: list[str] = []
    if leaks_hidden(p.hidden_objection, s.context_brief, s.opening_line, s.rep_goal):
        flags.append("leak")
    if p.difficulty in ("normal", "hard") and any(w in s.opening_line for w in COOPERATIVE):
        flags.append("too_cooperative")
    if re.search(r"\d+(\.\d+)?\s*%", s.context_brief + s.opening_line):
        flags.append("has_percent")
    if any(w in s.context_brief for w in TRAP_WORDS):
        flags.append("trap_words")
    if opening_counts[_norm(s.opening_line)] > 1:
        flags.append("duplicate_opening")
    if p.difficulty == "hard" and len(s.opening_line) > 40:
        flags.append("hard_opening_too_long")
    return flags


def risk_score(flags: list[str], llm_risk: int = 0) -> int:
    weight = {"leak": 5, "too_cooperative": 2, "has_percent": 3, "trap_words": 3, "duplicate_opening": 1,
              "hard_opening_too_long": 1}
    return sum(weight.get(f, 1) for f in flags) + max(0, min(10, llm_risk))
