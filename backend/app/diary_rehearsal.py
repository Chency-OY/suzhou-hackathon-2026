from __future__ import annotations

import re

from .models.diary import FieldDiary

# 日记中的医学判断不能进入医生角色设定。这里仅提取沟通体验与表达反馈。
_CLINICAL = re.compile(r"药|疗效|有效|安全性|副作用|不良反应|适应症|患者|病人|临床|试验|剂量|处方|价格|医保|\d|%")


def rehearsal_note(item: FieldDiary) -> str:
    if item.degraded:
        return ""
    impressions = [text.strip() for text in item.digest.first_impressions[:2]
                   if text.strip() and not _CLINICAL.search(text)]
    feedback = [text.strip() for text in item.digest.doctor_feedback[:2]
                if text.strip() and not _CLINICAL.search(text)]
    parts = [f"代表当时的感受：{text[:90]}" for text in impressions]
    parts.extend(f"据代表回忆的医生表达：{text[:90]}" for text in feedback)
    return "；".join(parts)[:300]
