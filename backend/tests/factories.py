from datetime import datetime

from app.models import DoctorPersona, Scenario, Session, Turn


def make_persona(**kw) -> DoctorPersona:
    base = {
        "id": "persona_001", "department": "endocrinology", "title": "副主任医师", "hospital_tier": "三甲",
        "style": "skeptical_challenger", "concerns": ["efficacy", "competitor_comparison"],
        "current_habit": "一线多用司美格鲁肽，对新药观望", "hidden_objection": "担心患者长期依从性和价格",
        "time_budget_turns": 6, "initial_trust": 40, "initial_patience": 60, "traps": ["none"],
        "backstory": "门诊以肥胖合并 2 型糖尿病患者为主。", "speech_habits": "爱打断，常说“你直接说重点”。",
        "difficulty": "hard",
    }
    base.update(kw)
    return DoctorPersona(**base)


def make_scenario(**kw) -> Scenario:
    base = {
        "id": "scn_001", "type": "first_visit", "persona_id": "persona_001",
        "rep_goal": "让医生了解产品并约下次沟通",
        "context_brief": "首次拜访内分泌科副主任。", "opening_line": "我只有几分钟，你说吧。",
        "success_criteria": ["探寻到医生关注点", "提出具体下一步"],
    }
    base.update(kw)
    return Scenario(**base)


def make_session(**kw) -> Session:
    base = {
        "id": "sess_001", "scenario_id": "scn_001", "rep_id": "rep_001",
        "started_at": datetime(2026, 10, 25, 9, 0),
        "turns": [
            Turn(idx=0, speaker="doctor", text="我只有几分钟，你说吧。"),
            Turn(idx=1, speaker="rep", text="张主任您好，我想先了解一下您门诊肥胖患者的用药情况。",
                 signals=["asked_open_question"]),
        ],
    }
    base.update(kw)
    return Session(**base)
