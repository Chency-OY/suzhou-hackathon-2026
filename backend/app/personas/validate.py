from __future__ import annotations

import re
from pathlib import Path

from ..models import DoctorPersona

CONCERN_KEYWORDS = {
    "efficacy": ["疗效", "降糖", "减重", "HbA1c", "体重", "达标", "有效", "效果"],
    "safety_gi": ["胃肠", "恶心", "呕吐", "腹泻", "安全", "耐受", "不良反应", "副作用"],
    "price_access": ["价格", "医保", "费用", "自费", "报销", "贵", "负担"],
    "long_term_evidence": ["长期", "远期", "随访", "结局", "证据", "样本", "研究", "数据"],
    "patient_adherence": ["依从", "坚持", "停药", "注射", "复诊", "脱落"],
    "competitor_comparison": ["司美", "替尔", "利拉", "度拉", "贝那", "对比", "头对头", "竞品", "现用",
                              "超越", "优势", "跟随"],
    "cv_benefit": ["心血管", "心脏", "血压", "MACE", "心梗", "卒中", "心率", "结局"],
}

DIFF_RANGES = {
    "easy": {"trust": (55, 75), "patience": (60, 85), "turns": (7, 12)},
    "normal": {"trust": (35, 55), "patience": (45, 65), "turns": (5, 9)},
    "hard": {"trust": (15, 40), "patience": (25, 50), "turns": (3, 7)},
}

_PCT = re.compile(r"\d+(\.\d+)?\s*%")
_PUNCT = re.compile(r"[\s，。,.、；;：:！!？?（）()“”\"'‘’\-—]+")


def load_blacklist(path: str | Path = "data/rubric/name_blacklist.txt") -> list[str]:
    p = Path(path)
    if not p.exists():
        return []
    return [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def normalize(p: DoctorPersona) -> DoctorPersona:
    """把数值字段限制到该难度的范围内（确定性修正，不拒绝）。"""
    r = DIFF_RANGES[p.difficulty]
    return p.model_copy(update={
        "initial_trust": _clamp(p.initial_trust, *r["trust"]),
        "initial_patience": _clamp(p.initial_patience, *r["patience"]),
        "time_budget_turns": _clamp(p.time_budget_turns, *r["turns"]),
    })


def _text(p: DoctorPersona) -> str:
    return f"{p.current_habit} {p.hidden_objection} {p.backstory} {p.speech_habits}"


def validate_persona(p: DoctorPersona, blacklist: list[str] | None = None) -> list[str]:
    """返回问题列表；空列表表示通过。"""
    issues: list[str] = []
    if not 10 <= len(p.hidden_objection) <= 80:
        issues.append("hidden_objection 长度应为 10~80 字")
    if not 15 <= len(p.backstory) <= 200:
        issues.append("backstory 长度应为 15~200 字")
    if not 6 <= len(p.current_habit) <= 80:
        issues.append("current_habit 长度应为 6~80 字")
    if not 4 <= len(p.speech_habits) <= 80:
        issues.append("speech_habits 长度应为 4~80 字")
    kws = [k for c in p.concerns for k in CONCERN_KEYWORDS.get(c, [])]
    if not any(k in p.hidden_objection for k in kws):
        issues.append("hidden_objection 与 concerns 不相关（未命中任何关键词）")
    if p.difficulty == "hard" and all(t == "none" for t in p.traps) and "打断" not in p.speech_habits:
        issues.append("hard 难度需包含 traps 或打断习惯")
    if p.department == "hepatology" and p.difficulty != "easy" and "off_label_bait" not in p.traps:
        pass  # 允许，但选择阶段会优先保留带 off_label_bait 的画像
    text = _text(p)
    if _PCT.search(text):
        issues.append("包含百分比数据")
    for w in (blacklist or []):
        if w in text:
            issues.append(f"命中黑名单：{w}")
            break
    return issues


def _grams(s: str) -> set[str]:
    s = _PUNCT.sub("", s)
    return {s[i:i + 2] for i in range(len(s) - 1)}


def similarity(a: DoctorPersona, b: DoctorPersona) -> float:
    ga, gb = _grams(a.hidden_objection + a.current_habit + a.backstory), _grams(
        b.hidden_objection + b.current_habit + b.backstory)
    return len(ga & gb) / len(ga | gb) if ga | gb else 0.0


def dedup(personas: list[DoctorPersona], threshold: float = 0.55
          ) -> tuple[list[DoctorPersona], list[tuple[DoctorPersona, str]]]:
    kept: list[DoctorPersona] = []
    dropped: list[tuple[DoctorPersona, str]] = []
    for p in personas:
        dup = next((k for k in kept if (k.department, k.style, k.hidden_objection) ==
                    (p.department, p.style, p.hidden_objection) or similarity(k, p) >= threshold), None)
        if dup:
            dropped.append((p, f"与 {dup.id} 重复"))
        else:
            kept.append(p)
    return kept, dropped
