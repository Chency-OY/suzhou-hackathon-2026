"""预筛场景：规则 + 模型质检，输出 data/scenarios/prescreen.json。
--auto-fix-leaks：对规则判定为 leak 的场景自动重生成（至多 2 次），其余只标记不改动。"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "backend")
from pydantic import BaseModel  # noqa: E402

from app.llm import BudgetExceeded, get_provider, load_prompt, structured_call  # noqa: E402
from app.models import DoctorPersona, Scenario  # noqa: E402
from app.scenarios.generate import _norm, generate_one  # noqa: E402
from app.scenarios.review import PRESCREEN_PATH, heuristic_flags, risk_score  # noqa: E402


class LLMReview(BaseModel):
    leak: bool = False
    too_cooperative: bool = False
    fabricated_data: bool = False
    style_mismatch: bool = False
    risk: int = 0
    note: str = ""


def load(path, cls):
    p = Path(path)
    return [cls.model_validate_json(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-llm", action="store_true", help="只用规则预筛")
    ap.add_argument("--auto-fix-leaks", action="store_true")
    args = ap.parse_args()

    personas = {p.id: p for p in load("data/personas/personas.jsonl", DoctorPersona)}
    scenarios = load("data/scenarios/scenarios.jsonl", Scenario)
    if not scenarios:
        print("没有场景。")
        return 2
    provider = None if args.no_llm else get_provider()
    if provider is not None and provider.name == "mock":
        print("当前为 mock，改为只用规则预筛。")
        provider = None
    prompt = load_prompt("scenario_review")

    counts = Counter(_norm(s.opening_line) for s in scenarios)
    result: dict[str, dict] = {}
    changed = False
    try:
        for i, s in enumerate(scenarios):
            p = personas[s.persona_id]
            flags = heuristic_flags(p, s, counts)
            if args.auto_fix_leaks and "leak" in flags and provider is not None:
                for _ in range(2):
                    draft, _reason = generate_one(provider, p, s.type)
                    if draft is not None:
                        s = Scenario(id=s.id, type=s.type, persona_id=p.id, source="generated", **draft.model_dump())
                        scenarios[i] = s
                        flags = heuristic_flags(p, s, counts)
                        changed = True
                        if "leak" not in flags:
                            break
            llm = LLMReview()
            if provider is not None:
                user = prompt.render(persona_json=p.model_dump_json(indent=2, exclude={"id"}), type=s.type,
                                     rep_goal=s.rep_goal, context_brief=s.context_brief, opening_line=s.opening_line)
                llm, _deg = structured_call(provider, prompt_name="scenario_review", system="你是严格输出 JSON 的质检员。",
                                            messages=[{"role": "user", "content": user}], model_cls=LLMReview,
                                            fallback=LLMReview(), max_retries=1, temperature=0.2)
                for k in ("leak", "too_cooperative", "fabricated_data", "style_mismatch"):
                    if getattr(llm, k) and k not in flags:
                        flags.append("llm_" + k)
            result[s.id] = {"flags": flags, "risk": risk_score(flags, llm.risk), "note": llm.note}
            print(s.id, result[s.id])
    except BudgetExceeded:
        print("预算耗尽，已保存已完成部分。")
    PRESCREEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    PRESCREEN_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if changed:
        Path("data/scenarios/scenarios.jsonl").write_text(
            "\n".join(s.model_dump_json() for s in scenarios) + "\n", encoding="utf-8")
        print("已自动重生成部分泄露场景，请重新运行 python scripts/seed.py 入库。")
    top = sorted(result.items(), key=lambda kv: -kv[1]["risk"])[:5]
    print("风险最高 5 个：", [(k, v["risk"], v["flags"]) for k, v in top])
    return 0


if __name__ == "__main__":
    sys.exit(main())
