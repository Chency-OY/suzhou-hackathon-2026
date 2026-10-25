from __future__ import annotations

import json
import logging
import math
from collections import Counter
from pathlib import Path

from pydantic import BaseModel

from ..llm import BudgetExceeded, LLMProvider, load_prompt, structured_call
from ..models import DoctorPersona
from .select import DEPT_RATIO, DIFF_RATIO, _lr, compute_quotas, select_personas
from .validate import dedup, load_blacklist, normalize, validate_persona

log = logging.getLogger(__name__)

DEPT_CN = {"endocrinology": "内分泌科", "cardiology": "心血管内科", "hepatology": "消化/肝病科"}
DEPT_ABBR = {"endocrinology": "endo", "cardiology": "cardio", "hepatology": "hepa"}
DEPT_CONTEXT = {
    "endocrinology": "门诊以 2 型糖尿病、肥胖合并代谢异常患者为主；医生熟悉 GLP-1 类药物，对降糖达标、"
                     "体重管理、胃肠道反应、长期用药依从性、医保与自费较敏感；常见现用方案包括司美格鲁肽、"
                     "度拉糖肽、利拉鲁肽等。",
    "cardiology": "门诊以高血压、冠心病、心衰、合并肥胖或代谢综合征的患者为主；更关注心血管获益证据、"
                  "对心率血压的影响、与现有心血管用药的关系；对缺乏心血管结局数据的新药审慎。",
    "hepatology": "门诊以脂肪肝（MAFLD/MASLD）、慢性肝病、肥胖相关肝脏问题为主；医生关心减重对肝脏脂肪和"
                  "纤维化的影响，可能主动询问药品在脂肪肝上的证据或用法，容易诱导代表谈未获批适应症。",
}
STYLES = ["rigorous_evidence", "busy_efficient", "skeptical_challenger", "friendly_open", "conservative_habit"]


class PersonaBatch(BaseModel):
    personas: list[DoctorPersona]


def _digest(personas: list[DoctorPersona], n: int = 12) -> str:
    if not personas:
        return "（暂无）"
    return "\n".join(f"- {p.style}｜{p.hidden_objection[:30]}｜{p.backstory[:20]}" for p in personas[-n:])


def generate_candidates(provider: LLMProvider, n_candidates: int, batch: int = 5,
                        dept_ratio: dict[str, float] = DEPT_RATIO,
                        diff_ratio: dict[str, float] = DIFF_RATIO) -> tuple[list[DoctorPersona], dict]:
    prompt = load_prompt("persona_gen")
    all_p: list[DoctorPersona] = []
    stats = {"batches": 0, "degraded_batches": 0, "budget_exceeded": False, "prompt_version": prompt.version}
    style_i = 0
    for dept, need in _lr(n_candidates, dept_ratio).items():
        got: list[DoctorPersona] = []
        max_attempts = math.ceil(need / batch) * 3
        attempts = 0
        while len(got) < need and attempts < max_attempts:
            attempts += 1
            count = min(batch, need - len(got))
            mix = _lr(count, diff_ratio)
            styles = [STYLES[(style_i + i) % len(STYLES)] for i in range(count)]
            style_i += count
            user = prompt.render(
                department=dept, department_cn=DEPT_CN[dept], count=count,
                difficulty_mix="，".join(f"{k}:{v}" for k, v in mix.items() if v),
                style_hint="、".join(styles), existing_digest=_digest(got or all_p),
                department_context=DEPT_CONTEXT[dept])
            try:
                res, degraded = structured_call(
                    provider, prompt_name="persona_gen", system="你是严格输出 JSON 的数据生成助手。",
                    messages=[{"role": "user", "content": user}], model_cls=PersonaBatch,
                    fallback=PersonaBatch(personas=[]), max_retries=2, temperature=0.9)
            except BudgetExceeded:
                stats["budget_exceeded"] = True
                log.error("预算耗尽，提前结束生成")
                return all_p + got, stats
            stats["batches"] += 1
            stats["degraded_batches"] += int(degraded)
            got += [p for p in res.personas if p.department == dept]
        all_p += got
    return all_p, stats


def run_pipeline(candidates: list[DoctorPersona], target: int, out_dir: str | Path = "data/personas",
                 blacklist_path: str = "data/rubric/name_blacklist.txt") -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    bl = load_blacklist(blacklist_path)
    rejects: list[dict] = []
    valid: list[DoctorPersona] = []
    for p in candidates:
        p = normalize(p)
        issues = validate_persona(p, bl)
        if issues:
            rejects.append({"persona": p.model_dump(), "reason": "；".join(issues)})
        else:
            valid.append(p)
    kept, dropped = dedup(valid)
    rejects += [{"persona": p.model_dump(), "reason": why} for p, why in dropped]
    quotas = compute_quotas(target)
    selected, shortfall = select_personas(kept, quotas)
    counters: Counter = Counter()
    final: list[DoctorPersona] = []
    for p in selected:
        counters[p.department] += 1
        final.append(p.model_copy(update={"id": f"persona_{DEPT_ABBR[p.department]}_{counters[p.department]:03d}"}))
    (out / "personas.jsonl").write_text("\n".join(p.model_dump_json() for p in final) + ("\n" if final else ""),
                                        encoding="utf-8")
    (out / "rejects.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rejects) + ("\n" if rejects else ""), encoding="utf-8")
    report = {
        "candidates": len(candidates), "valid": len(valid), "after_dedup": len(kept), "selected": len(final),
        "target": target, "shortfall": {f"{d}/{k}": v for (d, k), v in shortfall.items()},
        "reject_reasons": dict(Counter(r["reason"].split("：")[0] for r in rejects)),
        "dist_dept_diff": dict(Counter(f"{p.department}/{p.difficulty}" for p in final)),
        "dist_style": dict(Counter(p.style for p in final)),
        "off_label_hepatology": sum(1 for p in final if p.department == "hepatology" and "off_label_bait" in p.traps),
    }
    return report


def write_report(report: dict, stats: dict | None, path: str | Path = "docs/PERSONA_REPORT.md") -> None:
    lines = ["# 画像合成报告", ""]
    lines += [f"- {k}: {v}" for k, v in report.items() if not isinstance(v, dict)]
    for k, v in report.items():
        if isinstance(v, dict):
            lines += ["", f"## {k}", ""] + ([f"- {a}: {b}" for a, b in sorted(v.items())] or ["- 无"])
    if stats:
        lines += ["", "## 生成统计", ""] + [f"- {k}: {v}" for k, v in stats.items()]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
