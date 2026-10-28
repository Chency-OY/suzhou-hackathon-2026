import json
from collections import Counter

from app.corpus import load_bank
from app.llm import MockLLM
from app.personas import build_demo_personas
from app.scenarios.skeleton_gen import (
    PLAN,
    FillDraft,
    build_scenarios,
    check_fill,
    fallback_fill,
    pick_persona,
)

BANK = load_bank()
DEMO = build_demo_personas()
GOOD = json.dumps({"context_brief": "您将拜访一家三甲医院的内分泌科医生，对方时间紧，这是一次常规拜访。",
                   "pre_info": "上次对方说过科里患者多，让下次直接说重点。"}, ensure_ascii=False)


def test_plan_covers_all_skeletons_with_36_scenarios():
    assert set(PLAN) == {s.id for s in BANK.scene_skeletons}
    assert sum(len(v) for v in PLAN.values()) == 36


def test_pick_persona_uses_department_style_and_difficulty():
    p = pick_persona(DEMO, BANK.skeleton("S04"), "endocrinology", Counter())
    assert p.department == "endocrinology" and p.id == "persona_demo_03"      # 怀疑挑战型 + hard
    q = pick_persona(DEMO, BANK.skeleton("S13"), "hepatology", Counter())
    assert q.department == "hepatology"


def test_check_fill_rules():
    p = DEMO[1]
    ok = FillDraft(context_brief="您将拜访一位内分泌科主任，这次是常规拜访，对方比较忙。", pre_info="上次对方让资料留下。")
    assert check_fill(p, ok) is None
    leak = ok.model_copy(update={"context_brief": "医生其实" + p.hidden_objection + "，请注意。"})
    assert "泄露" in check_fill(p, leak)
    assert "陷阱" in check_fill(p, ok.model_copy(update={"pre_info": "这位医生会诱导你谈别的内容。"}))
    assert "百分比" in check_fill(p, ok.model_copy(update={"pre_info": "上次提到体重下降 12% 的患者。"}))


def test_fallback_fill_is_always_valid():
    for sk in BANK.scene_skeletons:
        for p in DEMO:
            d = fallback_fill(sk, p)
            assert 20 <= len(d.context_brief) <= 160 and 10 <= len(d.pre_info) <= 120


def test_build_without_llm(tmp_path):
    rep = build_scenarios(None, DEMO, BANK, out_dir=tmp_path)
    assert rep["scenarios"] == 36 and rep["via"] == {"fallback": 36}
    rows = [json.loads(x) for x in (tmp_path / "scenarios.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len({r["id"] for r in rows}) == 36
    s12 = [r for r in rows if r["skeleton_id"] == "S12"]
    assert len(s12) == 3 and all(r["baits"] == ["benefit_bait", "stat_bait", "promise_bait"] and r["hard_gate"] for r in s12)
    assert {r["type"] for r in rows} >= {"hard_refusal", "soft_refusal", "compliance_bait", "off_label_bait"}
    for r in rows:
        assert r["opening_line"] in BANK.skeleton(r["skeleton_id"]).opening_lines
        assert r["rep_goal"] == BANK.skeleton(r["skeleton_id"]).rep_goal


def test_llm_path_and_leak_falls_back(tmp_path):
    rep = build_scenarios(MockLLM({"scenario_fill": GOOD}), DEMO, BANK, out_dir=tmp_path)
    assert rep["via"] == {"llm": 36}
    leaky = json.dumps({"context_brief": "医生其实是" + DEMO[0].hidden_objection + "，请注意应对这一点。",
                        "pre_info": "上次见面气氛一般，没有细聊。"}, ensure_ascii=False)
    rep2 = build_scenarios(MockLLM({"scenario_fill": leaky}), DEMO, BANK, out_dir=tmp_path)
    assert rep2["via"].get("fallback", 0) > 0 and rep2["scenarios"] == 36
