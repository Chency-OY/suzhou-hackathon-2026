"""对话质量的可自动检查指标（用于冒烟和回归）。传入的 turns 需有 speaker/text/signals/meta 属性。"""
from __future__ import annotations

import re

from .guards import has_question, strip_event


def _norm(s: str) -> str:
    return re.sub(r"[\s，。,.、；;：:！!？?（）()“”\"'‘’\-—]+", "", strip_event(s))


def doctor_lines(turns) -> list[str]:
    return [strip_event(t.text) for t in turns if t.speaker == "doctor"]


def count_false_ignored(turns) -> int:
    """代表被标"回避提问"，但医生上一句其实不是提问。清洗之后这个数必须是 0。"""
    n = 0
    for i, t in enumerate(turns):
        if i > 0 and t.speaker == "rep" and "ignored_doctor_question" in t.signals and not has_question(turns[i - 1].text):
            n += 1
    return n


def count_repeats(turns) -> int:
    """同一场里医生说了重复的话（含开场白）。必须是 0。"""
    seen: set[str] = set()
    n = 0
    for t in turns:
        if t.speaker == "doctor":
            k = _norm(t.text)
            n += k in seen
            seen.add(k)
    return n


def avg_doctor_len(turns) -> float:
    lines = [x for x in doctor_lines(turns)]
    return sum(len(x) for x in lines) / len(lines) if lines else 0.0


def fallback_rate(turns) -> float:
    docs = [t for t in turns if t.speaker == "doctor" and t.meta.get("rep_turn_no", 0) > 0]
    return sum(1 for t in docs if t.meta.get("degraded")) / len(docs) if docs else 0.0


def signals_seen(turns) -> set[str]:
    return {s for t in turns if t.speaker == "rep" for s in t.signals}
