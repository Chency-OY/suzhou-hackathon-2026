from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .constants import DIMENSION_WEIGHTS

Department = Literal["endocrinology", "cardiology", "hepatology"]
Difficulty = Literal["easy", "normal", "hard"]
Title = Literal["主任医师", "副主任医师", "主治医师"]
HospitalTier = Literal["三甲", "二级", "社区"]
Style = Literal["rigorous_evidence", "busy_efficient", "skeptical_challenger",
                "friendly_open", "conservative_habit"]
Concern = Literal["efficacy", "safety_gi", "price_access", "long_term_evidence",
                  "patient_adherence", "competitor_comparison", "cv_benefit"]
Trap = Literal["off_label_bait", "competitor_bash_bait", "exaggeration_bait", "none"]
ScenarioType = Literal["first_visit", "post_conference", "safety_concern", "competitor_compare",
                       "time_pressure", "revisit_after_rejection", "off_label_bait",
                       "second_visit", "third_visit", "hard_refusal", "soft_refusal",
                       "turnover", "empty_handed", "compliance_bait", "followup_visit"]
Signal = Literal[
    "relevant_to_concern", "asked_open_question", "cited_evidence", "empathy_shown",
    "addressed_objection", "vague_or_generic", "pushy", "exaggeration",
    "off_label_claim", "competitor_bashing", "ignored_doctor_question", "proposed_next_step",
    "accepted_benefit", "disclosed_stat", "promised_outcome",
    "declined_boundary", "evaded_boundary",
]
EndReason = Literal["agreed_next_step", "doctor_left", "time_up", "rep_ended",
                   "materials_left", "referred", "soft_decline"]
FindingKind = Literal["strength", "issue", "missed_opportunity", "compliance_violation"]


class DoctorPersona(BaseModel):
    id: str
    department: Department
    title: Title
    hospital_tier: HospitalTier
    style: Style
    concerns: list[Concern] = Field(min_length=1)
    current_habit: str
    hidden_objection: str
    time_budget_turns: int = Field(ge=3, le=12)
    initial_trust: int = Field(ge=0, le=100)
    initial_patience: int = Field(ge=0, le=100)
    traps: list[Trap] = Field(default_factory=lambda: ["none"])
    backstory: str
    speech_habits: str
    difficulty: Difficulty


class Scenario(BaseModel):
    id: str
    type: ScenarioType
    persona_id: str
    rep_goal: str
    context_brief: str
    opening_line: str
    success_criteria: list[str] = Field(default_factory=list)
    source: Literal["generated", "playbook"] = "generated"
    skeleton_id: str | None = None
    setting: dict[str, Any] = Field(default_factory=dict)
    pre_info: str = ""
    turn_plan: list[str] = Field(default_factory=list)          # 内部：不得对外返回
    gold_moves: list[str] = Field(default_factory=list)         # 内部：不得对外返回
    compliance_checks: list[str] = Field(default_factory=list)  # 内部：不得对外返回
    baits: list[str] = Field(default_factory=list)              # 内部：不得对外返回
    events: list[str] = Field(default_factory=list)             # 内部：不得对外返回
    hard_gate: bool = False
    post_task: str | None = None


class DoctorState(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    trust: int = 50
    patience: int = 50
    engagement: int = 50
    revealed_hidden_objection: bool = False

    @field_validator("trust", "patience", "engagement", mode="before")
    @classmethod
    def _clamp(cls, v):
        return max(0, min(100, int(v)))


class Turn(BaseModel):
    idx: int = Field(ge=0)
    speaker: Literal["rep", "doctor"]
    text: str
    signals: list[Signal] = Field(default_factory=list)
    state_after: DoctorState | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class Session(BaseModel):
    id: str
    scenario_id: str
    rep_id: str
    started_at: datetime
    ended_at: datetime | None = None
    end_reason: EndReason | None = None
    pre_goal: str | None = None
    visit_note: str | None = None
    turns: list[Turn] = Field(default_factory=list)


class Finding(BaseModel):
    turn_idx: int = Field(ge=0)
    kind: FindingKind
    dimension: str
    quote: str = Field(min_length=1)
    explanation: str
    better_version: str | None = None


class Report(BaseModel):
    id: str
    session_id: str
    dimension_scores: dict[str, int]
    total_score: int = Field(ge=0, le=100)
    raw_total: int = Field(ge=0, le=100)
    capped_by_compliance: bool = False
    findings: list[Finding] = Field(default_factory=list)
    summary: str = ""
    next_practice_tips: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_scores(self):
        for k, v in self.dimension_scores.items():
            if k not in DIMENSION_WEIGHTS:
                raise ValueError(f"unknown dimension: {k}")
            if not 0 <= v <= DIMENSION_WEIGHTS[k]:
                raise ValueError(f"score out of range for {k}: {v}")
        return self

    def drop_invalid_findings(self, turns: list[Turn]) -> tuple[Report, int]:
        """丢弃 quote 不在对应回合原文中的 Finding（防止幻觉定位）。返回(新报告, 丢弃数量)。"""
        by_idx = {t.idx: t.text for t in turns}
        kept = [f for f in self.findings if f.turn_idx in by_idx and f.quote in by_idx[f.turn_idx]]
        return self.model_copy(update={"findings": kept}), len(self.findings) - len(kept)


class PlaybookCard(BaseModel):
    id: str
    title: str
    applicable_scenario_types: list[ScenarioType]
    applicable_departments: list[Department]
    situation: str
    effective_response_pattern: str
    example_lines: list[str] = Field(default_factory=list, max_length=3)
    evidence_session_ids: list[str] = Field(default_factory=list)
    avg_score_of_source: float = 0.0
    status: Literal["candidate", "approved"] = "candidate"
