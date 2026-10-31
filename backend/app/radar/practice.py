from __future__ import annotations

import re
from urllib.parse import urlparse

from ..models import RadarPracticeCue
from ..models.radar import AcademicRadar

_PROMPT_ATTACK = re.compile(r"忽略.{0,8}(?:指令|提示)|系统提示|提示词|你现在是|AI助手|开发者指令|override|prompt injection", re.IGNORECASE)


def practice_cue(radar: AcademicRadar) -> RadarPracticeCue | None:
    """从有逐字摘录的同名候选中取一条题材；不判定真实医生身份。"""
    if radar.web_status != "ok":
        return None
    sources = {item.id: item for item in radar.web_sources if item.name_in_source and item.hospital_in_source}
    for point in radar.answer_points:
        source = sources.get(point.source_id)
        if not source:
            continue
        title = " ".join(source.title.split())[:240]
        topic = title.replace(radar.doctor_name, "").replace(radar.hospital, "").strip(" -—:：·|")
        topic = re.sub(r"^(?:主任|医生|教授|院长)(?:的|：|:)?", "", topic).strip(" -—:：·|")[:180]
        url = urlparse(source.url)
        if (len(topic) < 4 or _PROMPT_ATTACK.search(title) or url.scheme != "https" or not url.hostname
                or len(point.evidence_quote.strip()) < 8):
            continue
        return RadarPracticeCue(title=title, topic=topic, source_url=source.url,
                                evidence_quote=point.evidence_quote)
    return None
