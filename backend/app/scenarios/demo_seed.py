"""离线兜底：不调用真实模型，用确定性草稿生成演示场景（与 personas 的 --demo 对应）。

MockLLM 的 callable 从渲染后的 prompt 中解析出科室/风格/难度/场景类型，
返回一份能通过 check_draft（不泄露隐藏异议、无陷阱字眼、无百分比）的固定草稿。
"""
from __future__ import annotations

import json
import re

from ..llm import MockLLM

REP_GOAL = "让医生了解产品的机制与已获批适用人群，并约定下一次学术沟通"

DEPT_CONTEXT_BRIEF = {
    "endocrinology": "您将拜访一位内分泌科医生，门诊以合并超重或血糖控制不佳的患者为主，"
                     "此前仅有零星交流，本次希望介绍产品并了解医生的关注点。",
    "cardiology": "您将拜访一位心内科医生，门诊常见肥胖合并高血压的患者，医生对代谢类新药了解有限，"
                  "本次拜访希望建立初步认知并了解其现有用药习惯。",
    "hepatology": "您将拜访一位消化/肝病科医生，门诊脂肪肝合并肥胖患者较多，医生关注减重相关药物的进展，"
                  "本次希望交流产品已获批适应症范围内的信息。",
}

STYLE_OPENING = {
    "rigorous_evidence": "你好。我时间有限，你先说说核心信息和数据来源。",
    "busy_efficient": "我马上要看下一个病人，三句话讲完。",
    "skeptical_challenger": "又是来推新药的？先说说你们跟现有方案有什么本质区别。",
    "friendly_open": "你好你好，正好今天门诊刚空下来，你随便聊聊。",
    "conservative_habit": "我平时用药比较固定，你简单介绍一下吧。",
}


def _grab(pattern: str, text: str, default: str) -> str:
    m = re.search(pattern, text)
    return m.group(1) if m else default


def _demo_draft(messages) -> str:
    content = messages[-1]["content"]
    stype = _grab(r"场景类型\n(\w+)：", content, "first_visit")
    dept = _grab(r'"department": "(\w+)"', content, "endocrinology")
    style = _grab(r'"style": "(\w+)"', content, "friendly_open")
    criteria = ["探寻到医生关注点", "提出具体可执行的下一步"]
    if stype == "off_label_bait":
        criteria.append("不宣传未获批适应症，回应不超出说明书范围")
    if stype == "time_pressure":
        criteria.append("在被打断的情况下仍完成核心信息传递")
    draft = {
        "rep_goal": REP_GOAL,
        "context_brief": DEPT_CONTEXT_BRIEF.get(dept, DEPT_CONTEXT_BRIEF["endocrinology"]),
        "opening_line": STYLE_OPENING.get(style, STYLE_OPENING["friendly_open"]),
        "success_criteria": criteria,
    }
    return json.dumps(draft, ensure_ascii=False)


def build_demo_scenario_provider() -> MockLLM:
    return MockLLM({"scenario_gen": _demo_draft})
