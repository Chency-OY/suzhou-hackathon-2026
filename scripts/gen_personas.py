import argparse
import sys

sys.path.insert(0, "backend")
from app.llm import get_provider  # noqa: E402
from app.personas import build_demo_personas, generate_candidates, run_pipeline, write_report  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=40)
    ap.add_argument("--candidates", type=int, default=300)
    ap.add_argument("--batch", type=int, default=5)
    ap.add_argument("--demo", action="store_true", help="不调用模型，使用内置 9 个手写画像（离线兜底）")
    args = ap.parse_args()

    stats = None
    if args.demo:
        candidates = build_demo_personas()
    else:
        provider = get_provider()
        if provider.name == "mock":
            print("LLM_PROVIDER=mock 无法生成画像。请配置 openai_compat，或加 --demo 使用内置画像。")
            return 2
        candidates, stats = generate_candidates(provider, args.candidates, args.batch)
    report = run_pipeline(candidates, args.target)
    write_report(report, stats)
    print({k: v for k, v in report.items() if not isinstance(v, dict)})
    if report["shortfall"]:
        print("配额缺口：", report["shortfall"], "（可提高 --candidates 重跑）")
    print("输出：data/personas/personas.jsonl, rejects.jsonl, docs/PERSONA_REPORT.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
