"""使用合成对话手动验证 DeepSeek 打法卡片提炼，不写入数据库。"""
from __future__ import annotations

from datetime import UTC, datetime

from app.llm import get_provider
from app.models import Scenario, Session, Turn
from app.personas import build_demo_personas
from app.playbook import card_is_safe, extract_card


def main() -> None:
    persona = build_demo_personas()[0]
    scenario = Scenario(id="synthetic_card_probe", program_id="general", type="first_visit",
                        persona_id=persona.id, rep_goal="先弄清对方顾虑，再提出合适的资料核对方式",
                        context_brief="完全虚构的沟通训练", opening_line="我不想听空泛的介绍。",
                        source="curated")
    turns = [Turn(idx=0, speaker="doctor", text=scenario.opening_line),
             Turn(idx=1, speaker="rep", text="理解您不想听空泛介绍。您最关注哪方面的资料？"),
             Turn(idx=2, speaker="doctor", text="我更关心后续随访是否清楚。"),
             Turn(idx=3, speaker="rep", text="您关注后续随访。我先查证正式资料，整理清楚后再请您看看，方便吗？")]
    session = Session(id="synthetic_card_session", scenario_id=scenario.id, rep_id="synthetic_user",
                      started_at=datetime.now(UTC), ended_at=datetime.now(UTC), end_reason="rep_ended",
                      turns=turns)
    card = extract_card(session, scenario, persona, get_provider(), "synthetic_card",
                        "synthetic_team", "synthetic_user", 85)
    if card is None or not card_is_safe(card):
        raise SystemExit("DeepSeek 没有返回可安全展示的卡片")
    print({"safe": True, "title": card.title, "examples": len(card.example_lines),
           "status": card.status})


if __name__ == "__main__":
    main()
