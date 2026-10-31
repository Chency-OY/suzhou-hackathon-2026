"""用虚构日记验证真实模型对重复表达的反应；不读写数据库。"""
from __future__ import annotations

from datetime import UTC, datetime

from app.diary_rehearsal import rehearsal_note
from app.llm import get_provider
from app.models.diary import DiaryDigest, FieldDiary
from app.sessions import SessionEngine, StateRules
from tests.factories import make_persona, make_scenario


def main() -> None:
    item = FieldDiary(id="synthetic_probe", owner_id="synthetic_user", created_at=datetime.now(UTC),
                      raw_text="这次拜访，医生说别用性价比。",
                      digest=DiaryDigest(summary="虚构沟通回忆", doctor_feedback=["医生说别用性价比"]))
    persona = make_persona(id="synthetic_persona", traps=["none"], initial_trust=45)
    scenario = make_scenario(id="synthetic_scenario", persona_id=persona.id, program_id="general")
    engine = SessionEngine(get_provider(), kb=None, rules=StateRules())
    session = engine.start(scenario, persona, "synthetic_user", diary_id=item.id)
    result = engine.step(session, scenario, persona, "我先讲讲性价比。", rehearsal_note=rehearsal_note(item))
    print({"triggered": session.turns[-1].meta.get("diary_wording_triggered"),
           "degraded": result.degraded, "doctor_reply": result.doctor_reply})
    if not session.turns[-1].meta.get("diary_wording_triggered") or result.degraded:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
