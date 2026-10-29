from types import SimpleNamespace as NS

from app.sessions.metrics import (
    avg_doctor_len,
    count_false_ignored,
    count_repeats,
    fallback_rate,
    signals_seen,
)


def T(speaker, text, signals=(), meta=None):
    return NS(speaker=speaker, text=text, signals=list(signals), meta=meta or {})


def test_false_ignored_counts_only_when_doctor_did_not_ask():
    turns = [T("doctor", "我现在用得挺好的，不用换。"), T("rep", "您好", ["ignored_doctor_question"]),
             T("doctor", "你这数据哪来的？"), T("rep", "稍后给您", ["ignored_doctor_question"])]
    assert count_false_ignored(turns) == 1


def test_repeats_ignore_punctuation_and_events():
    turns = [T("doctor", "三分钟，说重点。"), T("rep", "x"), T("doctor", "（接电话）三分钟说重点"), T("doctor", "嗯。")]
    assert count_repeats(turns) == 1


def test_length_fallback_and_signals():
    turns = [T("doctor", "一二三四五", meta={"rep_turn_no": 0}), T("rep", "x", ["cited_evidence"]),
             T("doctor", "一二三", meta={"rep_turn_no": 1, "degraded": True}),
             T("doctor", "一二三四五六七", meta={"rep_turn_no": 2, "degraded": False})]
    assert avg_doctor_len(turns) == 5.0
    assert fallback_rate(turns) == 0.5
    assert signals_seen(turns) == {"cited_evidence"}
    assert avg_doctor_len([]) == 0.0 and fallback_rate([]) == 0.0
