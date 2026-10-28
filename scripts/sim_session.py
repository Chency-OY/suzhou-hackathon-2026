"""用脚本化的"好/差"代表对 3 个骨架场景各跑一场，输出 docs/SAMPLE_SESSIONS.md。
真实模型下每场约 6 轮、每轮 2 次调用，用量很小。"""
import re
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
    "行，那改天我请您吃个饭，您放心。",
    "您放心用，量上我这边保证给您支持。",
]

# 按骨架选场景：S04 硬拒绝、S12 合规诱导、S08 副作用质疑
WANT_SKELETONS = ["S04", "S12", "S08"]
EVENT = re.compile(r"^（[^）]*）")


def pick(scenarios, personas):
    out = []
    for sk in WANT_SKELETONS:
        for s in scenarios:
            if s.skeleton_id == sk:
                out.append(s)
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


def doctor_metrics(sess) -> tuple[list[str], int]:
    """返回（去掉环境事件后的医生台词, 兜底回合数）。"""
    texts, degraded = [], 0
    for t in sess.turns:
        if t.speaker != "doctor":
            continue
        texts.append(EVENT.sub("", t.text).strip())
        degraded += int(bool((t.meta or {}).get("degraded")))
    return texts, degraded


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
    all_texts: list[str] = []
    all_degraded = 0
    for s in chosen:
        p = personas[s.persona_id]
        lines += [f"## {s.id}｜{p.department}｜{p.difficulty}｜{s.type}｜骨架 {s.skeleton_id}", ""]
        for label, script in (("好代表", GOOD), ("差代表", BAD)):
            sess, deg = run(engine, s, p, script)
            lines += render(sess, label, deg)
            final = [t.state_after for t in sess.turns if t.state_after][-1]
            texts, fb = doctor_metrics(sess)
            all_texts += texts
            all_degraded += fb
            avg_len = sum(len(x) for x in texts) / len(texts) if texts else 0.0
            fb_rate = fb / len(texts) if texts else 0.0
            summary.append((s.id, label, final.trust, final.patience, sess.end_reason, deg,
                            f"{avg_len:.1f}", f"{fb_rate:.0%}"))
    avg_all = sum(len(x) for x in all_texts) / len(all_texts) if all_texts else 0.0
    rate_all = all_degraded / len(all_texts) if all_texts else 0.0
    lines += ["## 汇总", "",
              "| 场景 | 代表 | 信任 | 耐心 | 结束原因 | 降级回合 | 医生平均字数 | 兜底率 |",
              "|---|---|---|---|---|---|---|---|"]
    lines += [f"| {a} | {b} | {c} | {d} | {e} | {f} | {g} | {h} |" for a, b, c, d, e, f, g, h in summary]
    lines += ["", f"- 自然度：医生台词平均字数 **{avg_all:.1f}**（判据 ≤ 35）",
              f"- 自然度：兜底率 **{rate_all:.0%}**（判据 ≤ 20%）",
              "", f"token 用量：{get_tracker().summary()}"]
    Path("docs/SAMPLE_SESSIONS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("已输出 docs/SAMPLE_SESSIONS.md")
    good = [s for s in summary if s[1] == "好代表"]
    bad = [s for s in summary if s[1] == "差代表"]
    checks: list[tuple[str, bool]] = []
    if provider.name != "mock":
        checks.append(("好代表最终信任度高于差代表", all(g[2] > b[2] for g, b in zip(good, bad))))
        checks.append((f"医生台词平均字数 ≤ 35（实测 {avg_all:.1f}）", avg_all <= 35))
        checks.append((f"兜底率 ≤ 20%（实测 {rate_all:.0%}）", rate_all <= 0.20))
    for name, passed in checks:
        print(f"{'✔' if passed else '✘'} {name}")
    ok = all(v for _, v in checks)
    if not ok:
        print("未通过：", "；".join(n for n, v in checks if not v))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
