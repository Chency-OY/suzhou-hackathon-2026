import json
import re

from app.llm import MockLLM
from app.personas import (
    build_demo_personas,
    compute_quotas,
    dedup,
    generate_candidates,
    normalize,
    run_pipeline,
    select_personas,
    validate_persona,
)

from tests.factories import make_persona

DEMO = build_demo_personas()


def test_all_demo_personas_pass_validation():
    assert len(DEMO) == 9
    for p in DEMO:
        assert validate_persona(p) == [], (p.id, validate_persona(p))


def test_validate_flags_problems():
    assert any("百分比" in i for i in validate_persona(make_persona(backstory="患者体重下降 12% 之后停药的病例")))
    assert any("黑名单" in i for i in validate_persona(make_persona(backstory="曾在协和进修多年的医生"), ["协和"]))
    assert any("不相关" in i for i in validate_persona(make_persona(
        concerns=["cv_benefit"], hidden_objection="不喜欢代表穿得太花哨影响判断")))
    bad_hard = make_persona(difficulty="hard", traps=["none"], speech_habits="语速平稳，很有耐心")
    assert any("hard" in i for i in validate_persona(bad_hard))


def test_normalize_clamps_to_difficulty_range():
    p = normalize(make_persona(difficulty="easy", initial_trust=5, initial_patience=100, time_budget_turns=3))
    assert (p.initial_trust, p.initial_patience, p.time_budget_turns) == (55, 85, 7)


def test_dedup_removes_near_duplicates():
    a = DEMO[0]
    clone = a.model_copy(update={"id": "x", "title": "主任医师"})
    kept, dropped = dedup([a, clone, DEMO[1]])
    assert [p.id for p in kept] == [a.id, DEMO[1].id] and "重复" in dropped[0][1]


def test_quotas_for_40():
    q = compute_quotas(40)
    assert sum(q.values()) == 40
    assert q[("endocrinology", "easy")] == 6 and q[("endocrinology", "normal")] == 8
    assert q[("cardiology", "hard")] == 3 and q[("hepatology", "normal")] == 4


def test_select_respects_quota_and_reports_shortfall():
    sel, short = select_personas(DEMO, compute_quotas(18))
    assert sel and sum(short.values()) >= 1          # 候选只有 9 个，必有缺口
    assert len({p.id for p in sel}) == len(sel)


def test_pipeline_terminates_and_dedups_with_repeating_llm(tmp_path):
    def fake(messages):
        dept = re.search(r"科室：(\w+)", messages[-1]["content"]).group(1)
        return json.dumps({"personas": [json.loads(p.model_dump_json()) for p in DEMO if p.department == dept]},
                          ensure_ascii=False)

    mock = MockLLM({"persona_gen": fake})
    cands, stats = generate_candidates(mock, n_candidates=30, batch=5)
    assert stats["batches"] > 0 and len(cands) >= 9           # 循环必须有限终止
    report = run_pipeline(cands, target=40, out_dir=tmp_path, blacklist_path="data/rubric/name_blacklist.txt")
    assert report["selected"] == 9 and report["shortfall"]
    lines = (tmp_path / "personas.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 9 and json.loads(lines[0])["id"].startswith("persona_")
    assert "重复" in (tmp_path / "rejects.jsonl").read_text(encoding="utf-8")
