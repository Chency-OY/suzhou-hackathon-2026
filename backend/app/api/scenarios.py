from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..db import Repo
from ..deps import get_repo
from ..models import DoctorPersona, Scenario

router = APIRouter(prefix="/api")

STYLE_HINTS = {
    "rigorous_evidence": "严谨循证型：重视数据与文献出处",
    "busy_efficient": "忙碌效率型：时间紧，喜欢直奔重点",
    "skeptical_challenger": "怀疑挑战型：爱质疑、爱对比",
    "friendly_open": "友好开放型：愿意交流",
    "conservative_habit": "保守惯性型：习惯既有方案",
}


class PersonaPublic(BaseModel):
    department: str
    title: str
    hospital_tier: str
    style_hint: str
    difficulty: str


PUBLIC_FIELDS = {"id", "type", "persona_id", "rep_goal", "context_brief", "opening_line", "success_criteria",
                 "source", "skeleton_id", "setting", "pre_info", "hard_gate", "post_task"}


class ScenarioItem(BaseModel):
    id: str
    type: str
    persona_id: str
    rep_goal: str
    context_brief: str
    opening_line: str
    success_criteria: list[str]
    source: str
    skeleton_id: str | None = None
    setting: dict = {}
    pre_info: str = ""
    hard_gate: bool = False
    post_task: str | None = None
    department: str
    difficulty: str


class ScenarioDetail(ScenarioItem):
    persona_public: PersonaPublic


def _public(p: DoctorPersona) -> PersonaPublic:
    return PersonaPublic(department=p.department, title=p.title, hospital_tier=p.hospital_tier,
                         style_hint=STYLE_HINTS[p.style], difficulty=p.difficulty)


def _item(s: Scenario, p: DoctorPersona) -> ScenarioItem:
    return ScenarioItem(**s.model_dump(include=PUBLIC_FIELDS), department=p.department, difficulty=p.difficulty)


@router.get("/scenarios", response_model=list[ScenarioItem])
def list_scenarios(dept: str | None = None, difficulty: str | None = None,
                   type_: str | None = Query(None, alias="type"), repo: Repo = Depends(get_repo)):
    personas = {p.id: p for p in repo.list(DoctorPersona)}
    out = []
    for s in repo.list(Scenario):
        p = personas.get(s.persona_id)
        if p is None:
            continue
        if (dept and p.department != dept) or (difficulty and p.difficulty != difficulty) or (
                type_ and s.type != type_):
            continue
        out.append(_item(s, p))
    return out


@router.get("/scenarios/{scenario_id}", response_model=ScenarioDetail)
def get_scenario(scenario_id: str, repo: Repo = Depends(get_repo)):
    s = repo.get(Scenario, scenario_id)
    p = repo.get(DoctorPersona, s.persona_id) if s else None
    if not s or not p:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "场景不存在"}})
    return ScenarioDetail(**_item(s, p).model_dump(), persona_public=_public(p))
