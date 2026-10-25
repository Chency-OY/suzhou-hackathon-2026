from __future__ import annotations

from collections import Counter

from ..models import DoctorPersona

DEPT_RATIO = {"endocrinology": 0.5, "cardiology": 0.25, "hepatology": 0.25}
DIFF_RATIO = {"easy": 0.3, "normal": 0.4, "hard": 0.3}


def _lr(total: int, ratios: dict[str, float]) -> dict[str, int]:
    raw = {k: round(total * r, 9) for k, r in ratios.items()}
    base = {k: int(v) for k, v in raw.items()}
    rem = total - sum(base.values())
    for k in sorted(raw, key=lambda k: raw[k] - base[k], reverse=True)[:rem]:
        base[k] += 1
    return base


def compute_quotas(total: int, dept_ratio: dict[str, float] = DEPT_RATIO,
                   diff_ratio: dict[str, float] = DIFF_RATIO) -> dict[tuple[str, str], int]:
    out: dict[tuple[str, str], int] = {}
    for dept, n in _lr(total, dept_ratio).items():
        for diff, m in _lr(n, diff_ratio).items():
            out[(dept, diff)] = m
    return out


def select_personas(personas: list[DoctorPersona], quotas: dict[tuple[str, str], int],
                    min_off_label_hepatology: int = 5) -> tuple[list[DoctorPersona], dict[tuple[str, str], int]]:
    """按 (科室, 难度) 配额选取；格内优先保证风格多样；肝病科优先保留带 off_label_bait 的画像。
    返回 (选中列表, 缺口{格: 缺少数量})。"""
    selected: list[DoctorPersona] = []
    shortfall: dict[tuple[str, str], int] = {}
    off_label_count = 0
    for (dept, diff), quota in sorted(quotas.items()):
        pool = [p for p in personas if p.department == dept and p.difficulty == diff]
        picked: list[DoctorPersona] = []
        styles: Counter = Counter()
        while pool and len(picked) < quota:
            def key(p: DoctorPersona, dept=dept, styles=styles, off_label_count=off_label_count):
                need_ol = dept == "hepatology" and off_label_count < min_off_label_hepatology
                return (0 if (need_ol and "off_label_bait" in p.traps) else 1, styles[p.style])
            best = min(pool, key=key)
            pool.remove(best)
            picked.append(best)
            styles[best.style] += 1
            if dept == "hepatology" and "off_label_bait" in best.traps:
                off_label_count += 1
        if len(picked) < quota:
            shortfall[(dept, diff)] = quota - len(picked)
        selected += picked
    return selected, shortfall
