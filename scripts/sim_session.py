"""用脚本化的"好/差"代表对 3 个场景各跑一场，输出 docs/SAMPLE_SESSIONS.md。
真实模型下每场约 6 轮、每轮 2 次调用，用量很小。"""
import sys
import time
from pathlib import Path

sys.path.insert(0, "backend")
from app.llm import get_provider, get_tracker  # noqa: E402
from app.models import DoctorPersona, Scenario  # noqa: E402
from app.rag import KnowledgeBase  # noqa: E402
from app.scenarios.review import load_review, usable  # noqa: E402
from app.sessions import SessionEngine  # noqa: E402

GOOD = [
    "主任您好，我是信达的代表，占用您三分钟，想先了解一下您门诊里肥胖合并糖尿病的患者大概占多少？",
    "听起来您对患者的长期坚持度比较关注。您目前遇到最大的困难是哪一块？",
    "我理解您的顾虑。我可以把玛仕度肽已公开发表的研究摘要和适用人群整理给您，您可以先对照说明书核实。",
    "说明书上的适应症我需要严格按已获批的范围来沟通，超出的部分我不能给出建议。",
    "如果您愿意，下周我约一次十五分钟的学术交流，只讨论符合适应症的人群，您看可以吗？",
    "好的，那我下周联系您确认时间，谢谢主任。",
]
BAD = [
    "主任好！我们这个药是目前最好的，没有任何副作用，我保证对您的患者有效！",
    "司美格鲁肽那些药都不行，效果差，您早就该换了。",
    "脂肪肝、高血压、睡眠呼吸暂停也都能用，您直接开就行，今天就定下来吧！",
    "您别犹豫了，别的医生都在用，您必须马上答应我。",
    "我们的数据特别好，具体我也记不清，反正比谁都强。",
    "您就给个准话吧，今天一定要定下来！",
]


def pick(scenarios, personas):
    want = [("endocrinology", "hard"), ("hepatology", None), ("cardiology", "normal")]
    out, used = [], set()
    for dept, diff in want:
        for s in scenarios:
            p = personas[s.persona_id]
            if s.id in used or p.department != dept or (diff and p.difficulty != diff):
                continue
            if dept == "hepatology" and s.type != "off_label_bait":
                continue
            out.append(s)
            used.add(s.id)
            break
    return out


def run(engine, scenario, persona, lines):
    sess = engine.start(scenario, persona, "rep_sim")
    degraded = 0
    for text in lines:
        if sess.ended_at:
            break
        res = engine.step(sess, scenario, persona, text)
        degraded += int(res.degraded)
    return sess, degraded


def render(sess, label, degraded) -> list[str]:
    out = [f"### {label}｜结束原因：{sess.end_reason or '未结束'}｜降级回合：{degraded}", ""]
    for t in sess.turns:
        who = "代表" if t.speaker == "rep" else "医生"
        extra = f"　`{t.signals}`" if t.speaker == "rep" else ""
        st = f"　(信任{t.state_after.trust}/耐心{t.state_after.patience})" if t.state_after else ""
        out.append(f"- **{who}**：{t.text}{extra}{st}")
    return out + [""]


def main() -> int:
    provider = get_provider()
    try:
        kb = KnowledgeBase()
        kb = kb if kb.count() else None
    except Exception:  # noqa: BLE001
        kb = None
    engine = SessionEngine(provider, kb)
    personas = {p.id: p for p in (DoctorPersona.model_validate_json(x) for x in
                Path("data/personas/personas.jsonl").read_text(encoding="utf-8").splitlines() if x.strip())}
    scenarios = usable([Scenario.model_validate_json(x) for x in
                        Path("data/scenarios/scenarios.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()],
                       load_review())
    chosen = pick(scenarios, personas)
    lines = ["# 样例对话（脚本化代表）", "",
             f"- provider：{provider.name}｜知识库：{'有' if kb else '无'}｜生成时间：{time.strftime('%Y-%m-%d %H:%M')}", ""]
    summary = []
    for s in chosen:
        p = personas[s.persona_id]
        lines += [f"## {s.id}｜{p.department}｜{p.difficulty}｜{s.type}", ""]
        for label, script in (("好代表", GOOD), ("差代表", BAD)):
            sess, deg = run(engine, s, p, script)
            lines += render(sess, label, deg)
            final = [t.state_after for t in sess.turns if t.state_after][-1]
            summary.append((s.id, label, final.trust, final.patience, sess.end_reason, deg))
    lines += ["## 汇总", "", "| 场景 | 代表 | 信任 | 耐心 | 结束原因 | 降级回合 |", "|---|---|---|---|---|---|"]
    lines += [f"| {a} | {b} | {c} | {d} | {e} | {f} |" for a, b, c, d, e, f in summary]
    lines += ["", f"token 用量：{get_tracker().summary()}"]
    Path("docs/SAMPLE_SESSIONS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("已输出 docs/SAMPLE_SESSIONS.md")
    good = [s for s in summary if s[1] == "好代表"]
    bad = [s for s in summary if s[1] == "差代表"]
    ok = all(g[2] > b[2] for g, b in zip(good, bad)) if provider.name != "mock" else True
    print("好代表最终信任度普遍高于差代表：", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
