"""用完全虚构的学术活动对话验证真实 DeepSeek 交叉核对；不写数据库。"""
from __future__ import annotations

from datetime import UTC, datetime

from app.academic_crosscheck import compare_academic
from app.llm import get_provider
from app.models.diary import DiaryDigest, FieldDiary
from app.models.radar import AcademicRadar, RadarAnswerPoint, RadarWebSource


def main() -> None:
    raw = "甲医生说他从未在星河论坛做过学术报告。"
    quote = "甲医生在星河论坛做了主题报告，介绍研究过程。"
    diary = FieldDiary(id="synthetic_probe", owner_id="synthetic_user", created_at=datetime.now(UTC),
                       doctor_name="甲医生", hospital="某某医院", raw_text=raw,
                       digest=DiaryDigest(summary="虚构拜访回忆"))
    radar = AcademicRadar(id="radar_synthetic", owner_id="synthetic_user", doctor_name="甲医生",
                          hospital="某某医院", searched_at=datetime.now(UTC), status="found", web_status="ok",
                          web_sources=[RadarWebSource(id="web_1", kind="conference", title="虚构论坛记录",
                                                      url="https://example.org/forum", name_in_source=True,
                                                      hospital_in_source=True)],
                          answer_points=[RadarAnswerPoint(kind="conference", statement="待确认的论坛记录",
                                                          source_id="web_1", evidence_quote=quote)])
    result = compare_academic(diary, radar, get_provider())
    valid = all(item.diary_quote in raw and item.source_quote in quote for item in result.tensions)
    print({"status": result.status, "tensions": len(result.tensions), "quotes_valid": valid,
           "identity_confirmed": False})
    if result.status != "compared" or not valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
