"""用六段合成对话进行真实模型评分校准；需在配置模型的环境手动运行。"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import yaml
from app.llm import get_provider
from app.models import Scenario, Session, Turn
from app.scoring import score_session


def main() -> None:
    cases = yaml.safe_load(Path("data/calibration/scoring_cases.yaml").read_text(encoding="utf-8"))["cases"]
    provider = get_provider()
    results = []
    for case in cases:
        turns = [Turn(idx=index, speaker=speaker, text=text)
                 for index, (speaker, text) in enumerate(case["turns"])]
        session = Session(id=f"cal_{case['id']}", scenario_id="calibration",
                          rep_id="synthetic_calibration", started_at=datetime.now(UTC),
                          ended_at=datetime.now(UTC), end_reason="rep_ended", turns=turns)
        scenario = Scenario(id="calibration", program_id="general", type="first_visit",
                            persona_id="synthetic_persona", rep_goal="了解医生关注并约定合规的后续交流",
                            context_brief="完全虚构的沟通训练校准", opening_line=turns[0].text,
                            source="curated")
        report = score_session(session, scenario, provider)
        results.append({"id": case["id"], "level": case["level"], "score": report.total_score,
                        "raw": report.raw_total, "mode": report.scoring_mode,
                        "capped": report.capped_by_compliance,
                        "in_range": case["expected"][0] <= report.total_score <= case["expected"][1],
                        "findings": len(report.findings)})
    means = {level: sum(item["score"] for item in results if item["level"] == level) / 2
             for level in ("strong", "medium", "weak")}
    passed = all(item["mode"] == "model" and item["in_range"] for item in results)
    passed = passed and means["strong"] > means["medium"] > means["weak"]
    print(json.dumps({"passed": passed, "means": means, "cases": results}, ensure_ascii=False))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
