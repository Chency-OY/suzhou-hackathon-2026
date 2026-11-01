from __future__ import annotations

import logging
import re
from datetime import UTC, datetime

import httpx

from .llm import LLMProvider, load_prompt, structured_call
from .models.diary import AcademicCrosscheck, AcademicCrossDraft, AcademicTension, FieldDiary
from .models.radar import AcademicRadar, RadarAnswerPoint, RadarWebSource

log = logging.getLogger(__name__)
POLICY_VERSION = "academic-tension-v2-explicit"
_ACADEMIC = re.compile(r"论文|研究|会议|论坛|演讲|报告|讲座|发表|参会|学术")
_MEDICAL = re.compile(r"药|疗效|副作用|剂量|治疗|处方|患者|适应症|安全性|不良反应")
_DENIED_ACTIVITY = re.compile(
    r"(?:从未|没有|未曾|并未|不曾).{0,18}(?:参加|参会|发表|演讲|做过|作过|做了|作了|作报告|做报告|讲过)"
    r"|未(?:参加|参会|发表|演讲|做报告|作报告)"
)
_AFFIRMED_ACTIVITY = re.compile(r"参加|参会|发表|演讲|做过|作过|做了|作了|做报告|作报告|讲过|出席")
_UNCONFIRMED_ACTIVITY = re.compile(r"计划|拟参加|拟发表|预计|即将|将于|可能|受邀|邀请")
_MISSING_EVIDENCE = re.compile(r"没有.{0,12}(?:证据|发现|查到|检索到|记录)|尚未找到|未检索到|未找到|未见|无法确认|不确定")
_YEAR = re.compile(r"(?:19|20)\d{2}")
_ACTIVITY_ENDINGS = ("论坛", "年会", "大会", "会议", "讲座", "论文", "研究", "报告", "演讲")
_GENERIC_ACTIVITIES = {"学术论坛", "学术会议", "学术报告", "主题报告", "研究报告", "公开讲座", "医学会议"}


def _same_named_activity(diary_quote: str, source_quote: str, title: str) -> bool:
    """Require an activity name shared by the diary, excerpt and source title."""
    for start in range(len(title)):
        for ending in _ACTIVITY_ENDINGS:
            position = title.find(ending, start)
            if position < 0:
                continue
            end = position + len(ending)
            if end < start + 4 or end > start + 18:
                continue
            name = title[start:end]
            if name not in _GENERIC_ACTIVITIES and name in diary_quote and name in source_quote:
                return True
    return False


def _explicit_opposition(diary_quote: str, source_quote: str, title: str) -> bool:
    if _UNCONFIRMED_ACTIVITY.search(diary_quote + source_quote) or _MISSING_EVIDENCE.search(diary_quote + source_quote):
        return False
    diary_years = set(_YEAR.findall(diary_quote))
    source_years = set(_YEAR.findall(source_quote))
    if diary_years and source_years and not diary_years & source_years:
        return False
    diary_denies = bool(_DENIED_ACTIVITY.search(diary_quote))
    source_denies = bool(_DENIED_ACTIVITY.search(source_quote))
    affirmative = source_quote if diary_denies else diary_quote
    return (diary_denies != source_denies and _AFFIRMED_ACTIVITY.search(affirmative) is not None
            and _same_named_activity(diary_quote, source_quote, title))


def _sources(radar: AcademicRadar) -> dict[str, tuple[RadarWebSource, list[RadarAnswerPoint]]]:
    indexed = {source.id: source for source in radar.web_sources
               if source.name_in_source and source.hospital_in_source and source.url.startswith("https://")}
    out: dict[str, tuple[RadarWebSource, list[RadarAnswerPoint]]] = {}
    for point in radar.answer_points:
        if point.source_id in indexed and len(point.evidence_quote.strip()) >= 8:
            if point.source_id not in out:
                out[point.source_id] = (indexed[point.source_id], [])
            out[point.source_id][1].append(point)
    return out


def compare_academic(diary: FieldDiary, radar: AcademicRadar | None,
                     provider: LLMProvider) -> AcademicCrosscheck:
    now = datetime.now(UTC)
    base = {"id": f"academic_{diary.id}", "diary_id": diary.id, "owner_id": diary.owner_id,
            "radar_id": radar.id if radar else "", "checked_at": now, "policy_version": POLICY_VERSION}
    if not radar:
        return AcademicCrosscheck(**base, status="no_radar",
                                  note="请先在学术雷达主动检索同一姓名和医院，再回到这里对照。")
    sources = _sources(radar)
    if not sources:
        return AcademicCrosscheck(**base, status="insufficient",
                                  note="雷达没有可用于逐字对照的同名学术摘录；不能据此判断日记对错。")
    if provider.name == "mock" and not provider.responses.get("academic_crosscheck"):
        return AcademicCrosscheck(**base, status="insufficient", note="模型暂不可用，未判断日记与网页是否有出入。")
    blocks = "\n".join(f"[{source_id}] {source.title}：" + "；".join(point.evidence_quote for point in points)
                       for source_id, (source, points) in sources.items())
    prompt = load_prompt("academic_crosscheck").render(diary=diary.raw_text[:4000], sources=blocks[:7000])
    try:
        draft, degraded = structured_call(
            provider, prompt_name="academic_crosscheck", system="你只输出可逐字核对的 JSON 学术线索对照。",
            messages=[{"role": "user", "content": prompt}], model_cls=AcademicCrossDraft,
            fallback=AcademicCrossDraft(), max_retries=1, temperature=0.0, max_tokens=650)
    except (RuntimeError, httpx.HTTPError):
        log.warning("学术线索交叉核对模型暂不可用")
        degraded, draft = True, AcademicCrossDraft()
    if degraded:
        return AcademicCrosscheck(**base, status="insufficient", note="模型暂不可用，未判断日记与网页是否有出入。")
    tensions = []
    seen = set()
    for item in draft.tensions:
        matched = sources.get(item.source_id)
        if not matched or (item.diary_quote, item.source_id) in seen:
            continue
        source, points = matched
        if (item.diary_quote not in diary.raw_text or
                not any(item.source_quote in point.evidence_quote for point in points) or
                not _ACADEMIC.search(item.diary_quote) or not _ACADEMIC.search(item.source_quote) or
                _MEDICAL.search(item.diary_quote) or _MEDICAL.search(item.source_quote) or
                not _explicit_opposition(item.diary_quote, item.source_quote, source.title)):
            continue
        seen.add((item.diary_quote, item.source_id))
        tensions.append(AcademicTension(diary_quote=item.diary_quote, source_id=item.source_id,
                                        source_quote=item.source_quote, source_title=source.title,
                                        source_url=source.url))
    note = ("找到可能有出入的同名学术线索；人物身份和网页内容均需人工核对。"
            if tensions else "未找到可逐字定位的明显出入；不能据此认定日记与网页一致。")
    return AcademicCrosscheck(**base, status="compared", tensions=tensions[:5], note=note)
