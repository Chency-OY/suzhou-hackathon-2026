"""用骨架库重新生成场景（旧文件先备份为 scenarios_v1.jsonl.bak）。
用法：python scripts/gen_scenarios_v2.py [--no-llm]"""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, "backend")
from app.corpus import load_bank, validate_bank  # noqa: E402
from app.llm import get_provider  # noqa: E402
from app.models import DoctorPersona  # noqa: E402
from app.scenarios.generate import write_scenario_report  # noqa: E402
from app.scenarios.skeleton_gen import build_scenarios  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-llm", action="store_true")
    args = ap.parse_args()
    bank = load_bank()
    errs = validate_bank(bank)
    if errs:
        print("骨架库校验失败：")
        print("\n".join(" - " + e for e in errs))
        return 1
    path = Path("data/personas/personas.jsonl")
    personas = [DoctorPersona.model_validate_json(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    provider = None if args.no_llm else get_provider()
    if provider is not None and provider.name == "mock":
        print("当前 LLM_PROVIDER=mock，改用确定性兜底文本（等同 --no-llm）。")
        provider = None
    old = Path("data/scenarios/scenarios.jsonl")
    if old.exists():
        shutil.copy(old, old.with_name("scenarios_v1.jsonl.bak"))
    report = build_scenarios(provider, personas, bank)
    write_scenario_report(report)
    print({k: report[k] for k in ("scenarios", "via", "budget_exceeded")})
    print("输出：data/scenarios/scenarios.jsonl, docs/SCENARIO_REPORT.md；下一步：python scripts/seed.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
