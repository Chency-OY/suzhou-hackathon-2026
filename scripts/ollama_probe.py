"""用服务器当前 LLM 配置做 10 次结构化调用，统计成功率与延迟，输出 docs/OLLAMA_PROBE.md"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "backend")
from app.llm import get_provider, get_tracker  # noqa: E402
from app.models import DoctorPersona  # noqa: E402
from app.scenarios import generate_one  # noqa: E402


def main() -> int:
    provider = get_provider()
    if provider.name == "mock":
        print("当前为 mock，无法探测。")
        return 2
    path = Path("data/personas/personas.jsonl")
    personas = [DoctorPersona.model_validate_json(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    types = ["first_visit", "competitor_compare", "safety_concern", "time_pressure", "off_label_bait"]
    rows, ok = [], 0
    for i in range(10):
        p, t = personas[i % len(personas)], types[i % len(types)]
        t0 = time.time()
        draft, reason = generate_one(provider, p, t, kb=None, max_attempts=1)
        dt = time.time() - t0
        ok += int(draft is not None)
        rows.append({"persona": p.id, "type": t, "ok": draft is not None, "reason": reason, "seconds": round(dt, 1)})
        print(rows[-1])
    avg = sum(r["seconds"] for r in rows) / len(rows)
    usage = get_tracker().summary()
    lines = ["# Ollama / 当前 LLM 能力探测", "", f"- provider: {provider.name}", f"- 成功率：{ok}/10（单次尝试，无重试）",
             f"- 平均耗时：{avg:.1f}s／次", f"- token 用量：{json.dumps(usage, ensure_ascii=False)}", "",
             "## 明细", ""] + [f"- {r}" for r in rows] + [
             "", "## 结论建议（由 GLM 填写）", "",
             "- 成功率 ≥ 8/10 且平均耗时 ≤ 10s：可考虑用作演示时的医生对话模型；",
             "- 否则：仅用于冒烟测试，演示使用云端模型（保留本地模型作为断网兜底）。"]
    Path("docs/OLLAMA_PROBE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
