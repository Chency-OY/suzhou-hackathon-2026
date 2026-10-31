from __future__ import annotations

import re

from .models.diary import FieldDiary

# 日记中的医学判断不能进入医生角色设定。这里仅提取沟通体验与表达反馈。
_CLINICAL = re.compile(
    r"药|产品|治疗|疗效|有效|安全|副作用|不良|适应|获批|禁忌|患者|病人|临床|试验|"
    r"剂量|处方|价格|医保|风险|诊断|症状|减重|降糖|血糖|心血管|随访|\d|%|"
    r"论文|会议|论坛|演讲|讲座|发表|参会|学术|研究"
)
_TITLE_NAME = re.compile(r"[\u3400-\u9fff]{1,4}(?:主任|医生|教授|院长)")
_INSTRUCTION = re.compile(r"忽略|系统提示|提示词|角色设定|越狱|指令|输出JSON", re.IGNORECASE)
_AVOID_WORDING = re.compile(
    r"(?:别用|别说|不要用|不要说|不喜欢(?:我)?说|讨厌(?:我)?说)"
    r"[‘’“”\"']?([\u3400-\u9fffA-Za-z]{2,12})"
)
_INTERRUPTED_WORDING = re.compile(r"一提([\u3400-\u9fffA-Za-z]{2,12})就(?:被打断|打断|皱眉|不耐烦)")


def _safe_observation(text: str, item: FieldDiary) -> str:
    text = text.strip()
    if not text or text not in item.raw_text or _CLINICAL.search(text) or _INSTRUCTION.search(text):
        return ""
    for value, replacement in ((item.doctor_name.strip(), "医生"), (item.hospital.strip(), "医院")):
        if len(value) >= 2:
            text = text.replace(value, replacement)
    return _TITLE_NAME.sub("医生", text)[:90]


def rehearsal_note(item: FieldDiary) -> str:
    if item.degraded:
        return ""
    impressions = [_safe_observation(text, item) for text in item.digest.first_impressions[:2]]
    feedback = [_safe_observation(text, item) for text in item.digest.doctor_feedback[:2]]
    parts = [f"代表当时的感受：{text}" for text in impressions if text]
    parts.extend(f"据代表回忆的医生表达：{text}" for text in feedback if text)
    return "；".join(parts)[:300]


def triggered_wording(note: str, rep_text: str) -> str:
    """只从已经去身份的主观反馈里找本轮再次使用的表达。"""
    for part in note.split("；"):
        if not part.startswith("据代表回忆的医生表达："):
            continue
        match = _AVOID_WORDING.search(part) or _INTERRUPTED_WORDING.search(part)
        if not match:
            continue
        phrase = match.group(1)
        for ending in ("这个说法", "这个词", "这种说法", "这词"):
            if phrase.endswith(ending):
                phrase = phrase[:-len(ending)]
                break
        if len(phrase) >= 2 and phrase.casefold() in rep_text.casefold():
            return phrase
    return ""
