from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator

from ..models.constants import SIGNALS

DEFAULT_DELTAS: dict[str, dict[str, int]] = {
    "relevant_to_concern": {"trust": 6, "engagement": 5},
    "asked_open_question": {"trust": 5, "engagement": 6},
    "cited_evidence": {"trust": 6},
    "empathy_shown": {"trust": 4},
    "addressed_objection": {"trust": 8, "patience": 3},
    "vague_or_generic": {"trust": -4, "patience": -6},
    "pushy": {"trust": -8, "patience": -10},
    "exaggeration": {"trust": -10},
    "off_label_claim": {"trust": -15, "patience": -10},
    "competitor_bashing": {"trust": -10},
    "ignored_doctor_question": {"trust": -8, "patience": -8},
    "proposed_next_step": {"trust": 3},
}


class StateRules(BaseModel):
    deltas: dict[str, dict[str, int]] = Field(default_factory=lambda: {k: dict(v) for k, v in DEFAULT_DELTAS.items()})
    reveal_min_trust: int = 55
    agree_min_trust: int = 80
    bait_min_rep_turns: int = 2
    bait_spacing_rep_turns: int = 2
    negative_signals: list[str] = Field(default_factory=lambda: ["pushy", "exaggeration", "off_label_claim",
                                                                 "competitor_bashing"])

    @model_validator(mode="after")
    def _check(self):
        for sig, d in self.deltas.items():
            if sig not in SIGNALS:
                raise ValueError(f"未知信号：{sig}")
            for k in d:
                if k not in ("trust", "patience", "engagement"):
                    raise ValueError(f"未知状态字段：{k}")
        for s in self.negative_signals:
            if s not in SIGNALS:
                raise ValueError(f"未知信号：{s}")
        return self


def load_rules(path: str | Path = "data/rubric/state_rules.yaml") -> StateRules:
    p = Path(path)
    if not p.exists():
        return StateRules()
    return StateRules(**(yaml.safe_load(p.read_text(encoding="utf-8")) or {}))
