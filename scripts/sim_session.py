"""自适应代表模拟器：用模型扮演"好代表/差代表"，与对话引擎真实对练，输出样例对话与质量指标。
用法：python scripts/sim_session.py     （需要真实模型；mock 下直接退出）"""
import sys
import time
from pathlib import Path

sys.path.insert(0, "backend")
from pydantic import BaseModel, Field  # noqa: E402

from app.llm import get_provider, get_tracker, load_prompt, structured_call  # noqa: E402
from app.models import DoctorPersona, Scenario  # noqa: E402
from app.rag import KnowledgeBase  # noqa: E402
from app.scenarios.review import load_review, usable  # noqa: E402
from app.sessions import SessionEngine  # noqa: E402
from app.sessions.engine import format_history  # noqa: E402
from app.sessions.metrics import (avg_doctor_len, count_false_ignored, count_repeats, fallback_rate,  # noqa: E402
                                  signals_seen)

LEVELS = {
    "good": ("水平较好：先认同医生再提问；只说有出处的信息，不夸大、不贬低竞品；医生试探饭局、赞助、处方量、"
             "范围外用法时，明确而友好地拒绝并转回学术（例如“这个我得婉拒，公司有规定，学术上的问题随时聊”）；"
             "时机合适时提出一个具体的下一步。"),
    "bad": ("水平较差：爱夸大和绝对化（比如保证有效、没有副作用），贬低竞品，必要时暗示范围外的用法；"
            "医生试探饭局、赞助或要支持时顺势答应并承诺放量；催促医生马上答应。"),
}
FALLBACK = {
    "good": ["您好，想先了解一下您门诊这类患者的情况。", "明白，我按说明书范围来说。", "那我下周再约您十五分钟，可以吗？"],
    "bad": ["我们这个药最好，没副作用，保证有效。", "别的药都不行，您早该换了。", "您今天就定下来吧。"],
}
TARGETS = ["S04", "S12", "S08", "S13"]
MAX_TURNS = 8
BAD_SIGNALS = {"accepted_benefit", "disclosed_stat", "promised_outcome", "evaded_boundary"}


class RepSay(BaseModel):
    say: str = Field(min_length=2, max_length=120)


def load(path, cls):
    f = Path(path)
    return [cls.model_validate_json(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]


def rep_say(provider, level, scenario, session, n) -> tuple[str, bool]:
    user = load_prompt("rep_bot").render(
        level_desc=LEVELS[level], rep_goal=scenario.rep_goal, context_brief=scenario.context_brief,
        pre_info=scenario.pre_info or "（无）", history=format_history(session.turns, 8))
    fb = FALLBACK[level][min(n, len(FALLBACK[level]) - 1)]
    out, degraded = structured_call(
        provider, prompt_name="rep_bot", system="你是严格输出 JSON 的角色扮演助手。",
        messages=[{"role": "user", "content": user}], model_cls=RepSay, fallback=RepSay(say=fb),
        max_retries=1, temperature=0.8)
    return out.say.strip(), degraded


def run(engine, provider, scenario, persona, level):
    sess = engine.start(scenario, persona, f"rep_sim_{level}")
    rep_fb = 0
    for i in range(MAX_TURNS):
        if sess.ended_at:
            break
        text, deg = rep_say(provider, level, scenario, sess, i)
        rep_fb += int(deg)
        engine.step(sess, scenario, persona, text)
    return sess, rep_fb


def final_trust(sess) -> int:
    return [t.state_after for t in sess.turns if t.state_after][-1].trust


def render(sess, label, rep_fb) -> list[str]:
    out = [f"### {label}｜结束原因：{sess.end_reason or '未结束'}｜代表兜底回合：{rep_fb}", ""]
    for t in sess.turns:
        st = f"　(信任{t.state_after.trust}/耐心{t.state_after.patience})" if t.state_after else ""
        if t.speaker == "rep":
            out.append(f"- **代表**：{t.text}　`{t.signals}`{st}")
        else:
            out.append(f"- **医生**：{t.text}　`意图={t.meta.get('intent')}`{st}")
    return out + [""]


def main() -> int:
    provider = get_provider()
    if provider.name == "mock":
        print("当前是 mock，无法做自适应模拟。请配置真实模型后再运行。")
        return 0
    try:
        kb = KnowledgeBase()
        kb = kb if kb.count() else None
    except Exception:  # noqa: BLE001
        kb = None
    engine = SessionEngine(provider, kb)
    personas = {p.id: p for p in load("data/personas/personas.jsonl", DoctorPersona)}
    scenarios = usable(load("data/scenarios/scenarios.jsonl", Scenario), load_review())
    chosen = [next((s for s in scenarios if s.skeleton_id == sid), None) for sid in TARGETS]
    chosen = [s for s in chosen if s]

    lines = ["# 样例对话（自适应代表模拟器）", "",
             f"- provider：{provider.name}｜知识库：{'有' if kb else '无'}｜{time.strftime('%Y-%m-%d %H:%M')}", ""]
    fails: list[str] = []
    all_turns: list = []
    wins = 0
    for s in chosen:
        p = personas[s.persona_id]
        lines += [f"## {s.id}｜{s.skeleton_id}｜{p.department}｜{p.difficulty}｜{s.type}", ""]
        res = {}
        for level in ("good", "bad"):
            sess, rep_fb = run(engine, provider, s, p, level)
            res[level] = sess
            all_turns += sess.turns
            lines += render(sess, "好代表" if level == "good" else "差代表", rep_fb)
            if count_false_ignored(sess.turns):
                fails.append(f"{s.id}/{level}：出现 {count_false_ignored(sess.turns)} 处“回避提问”误判")
            if count_repeats(sess.turns):
                fails.append(f"{s.id}/{level}：医生重复了 {count_repeats(sess.turns)} 句话")
        wins += int(final_trust(res["good"]) > final_trust(res["bad"]))
        sg, sb = signals_seen(res["good"].turns), signals_seen(res["bad"].turns)
        if s.skeleton_id == "S12":
            if "declined_boundary" not in sg:
                fails.append(f"{s.id}：好代表没有任何一次被识别为明确拒绝（declined_boundary）")
            if not (sb & BAD_SIGNALS):
                fails.append(f"{s.id}：差代表没有触发任何合规违规信号")
    if chosen and wins < len(chosen) - 1:
        fails.append(f"好代表信任度高于差代表的场景只有 {wins}/{len(chosen)}（要求至少 {len(chosen) - 1}）")
    avg, fb = avg_doctor_len(all_turns), fallback_rate(all_turns)
    if avg > 35:
        fails.append(f"医生平均字数 {avg:.1f} > 35")
    if fb > 0.2:
        fails.append(f"医生兜底率 {fb:.0%} > 20%")
    lines += ["## 汇总", "", f"- 好代表胜出：{wins}/{len(chosen)}", f"- 医生平均字数：{avg:.1f}",
              f"- 医生兜底率：{fb:.0%}", f"- 未通过项：{fails or '无'}", "", f"token 用量：{get_tracker().summary()}"]
    Path("docs/SAMPLE_SESSIONS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("已输出 docs/SAMPLE_SESSIONS.md；未通过项：", fails or "无")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
