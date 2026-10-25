import json

from app.llm import MockLLM
from app.personas import build_demo_personas
from app.scenarios import assign_types, check_draft, generate_one, leaks_hidden, run_scenarios
from app.scenarios.generate import ScenarioDraft

from tests.factories import make_persona

DEMO = build_demo_personas()
GOOD = {"rep_goal": "让医生了解产品定位并约定下一次学术沟通", "context_brief":
        "您将拜访一位内分泌科副主任医师，门诊以合并超重的 2 型糖尿病患者为主，这是双方第一次正式沟通。",
        "opening_line": "我只有几分钟，你直接说重点吧。", "success_criteria": ["探寻到医生关注点", "提出具体下一步"]}


def test_leak_detection():
    h = "担心患者对每周注射的长期坚持度，体重下降后容易自行停药"
    assert leaks_hidden(h, "医生其实担心患者对每周注射的长期坚持度")
    assert not leaks_hidden(h, "您将拜访一位内分泌科副主任医师，这是首次沟通")


def test_check_draft_rules():
    p = DEMO[0]
    assert check_draft(p, ScenarioDraft(**GOOD)) is None
    leaky = {**GOOD, "context_brief": "医生内心：" + p.hidden_objection + "，请注意。"}
    assert "泄露" in check_draft(p, ScenarioDraft(**leaky))
    trap = {**GOOD, "context_brief": "这位医生会诱导你谈论未获批的适应症，请小心应对他的提问。"}
    assert "陷阱" in check_draft(p, ScenarioDraft(**trap))


def test_assign_types_hepatology_off_label():
    hepa = [make_persona(id=f"h{i:02d}", department="hepatology",
                         traps=["off_label_bait"] if i < 6 else ["none"]) for i in range(10)]
    assigned = assign_types(hepa)
    ol = [p for p, t in assigned if t == "off_label_bait"]
    assert len(assigned) == 10 and len(ol) >= 4
    assert all("off_label_bait" in p.traps for p in ol)


def test_generate_one_retries_after_leak():
    p = DEMO[0]
    leaky = {**GOOD, "context_brief": "背景：" + p.hidden_objection + "，这是首次拜访沟通。"}
    mock = MockLLM({"scenario_gen": [json.dumps(leaky, ensure_ascii=False), json.dumps(GOOD, ensure_ascii=False)]})
    draft, reason = generate_one(mock, p, "first_visit")
    assert draft is not None and reason is None
    assert "上一次不合格" in mock.calls[1]["messages"][0]["content"]


def test_generate_one_gives_up(tmp_path):
    p = DEMO[0]
    mock = MockLLM({"scenario_gen": "not json"})
    draft, reason = generate_one(mock, p, "first_visit", max_attempts=2)
    assert draft is None and reason


def test_run_scenarios_writes_files(tmp_path):
    mock = MockLLM({"scenario_gen": json.dumps(GOOD, ensure_ascii=False)})
    report = run_scenarios(mock, DEMO, kb=None, out_dir=tmp_path)
    assert report["scenarios"] == 9 and report["rejected"] == 0
    rows = [json.loads(x) for x in (tmp_path / "scenarios.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["id"] for r in rows][:2] == ["scn_001", "scn_002"]
    assert {r["persona_id"] for r in rows} == {p.id for p in DEMO}
