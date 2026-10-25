import argparse
import sys
from pathlib import Path

sys.path.insert(0, "backend")
from app.llm import get_provider  # noqa: E402
from app.models import DoctorPersona  # noqa: E402
from app.rag import KnowledgeBase  # noqa: E402
from app.scenarios import run_scenarios, write_scenario_report  # noqa: E402
from app.scenarios.demo_seed import build_demo_scenario_provider  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="不调用真实模型，用内置演示草稿（离线兜底）")
    args = ap.parse_args()
    path = Path("data/personas/personas.jsonl")
    if not path.exists():
        print("缺少 data/personas/personas.jsonl，请先运行 make gen-personas（或 --demo）。")
        return 2
    if args.demo:
        provider = build_demo_scenario_provider()
    else:
        provider = get_provider()
        if provider.name == "mock":
            print("LLM_PROVIDER=mock 无法生成场景，请配置 openai_compat（或使用 --demo 离线演示）。")
            return 2
    personas = [DoctorPersona.model_validate_json(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    try:
        kb = KnowledgeBase()
        if kb.count() == 0:
            kb = None
    except Exception as e:  # noqa: BLE001
        print("知识库不可用，场景将不引用资料：", e)
        kb = None
    report = run_scenarios(provider, personas, kb)
    write_scenario_report(report)
    print({k: v for k, v in report.items() if not isinstance(v, dict)})
    print("输出：data/scenarios/scenarios.jsonl, rejects.jsonl, docs/SCENARIO_REPORT.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
