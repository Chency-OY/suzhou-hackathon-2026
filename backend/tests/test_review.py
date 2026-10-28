from collections import Counter

import pytest
from app.personas import build_demo_personas
from app.scenarios.review import (
    heuristic_flags,
    load_review,
    risk_score,
    save_review,
    set_status,
    status_of,
    usable,
)

from tests.factories import make_scenario

DEMO = build_demo_personas()


def test_review_roundtrip_and_usable(tmp_path):
    path = tmp_path / "review.json"
    assert load_review(path) == {}
    data: dict = {}
    set_status(data, "scn_002", "rejected", "太配合")
    set_status(data, "scn_003", "needs_fix")
    save_review(data, path)
    loaded = load_review(path)
    assert status_of(loaded, "scn_002") == "rejected" and status_of(loaded, "scn_999") == "pending"
    sc = [make_scenario(id=f"scn_00{i}") for i in (1, 2, 3)]
    assert [s.id for s in usable(sc, loaded)] == ["scn_001", "scn_003"]
    with pytest.raises(ValueError):
        set_status(data, "x", "bogus")


def test_heuristic_flags():
    p = DEMO[2]   # hard
    ok = make_scenario(persona_id=p.id, opening_line="我只有三分钟，直接说。",
                       context_brief="您将拜访一位二级医院的内分泌科副主任医师，这是第一次沟通。")
    assert heuristic_flags(p, ok, Counter()) == []
    bad = make_scenario(persona_id=p.id, opening_line="欢迎欢迎，请讲，没问题！",
                        context_brief="医生内心：" + p.hidden_objection + "；体重下降 12% 很显著。")
    flags = heuristic_flags(p, bad, Counter())
    assert {"leak", "too_cooperative", "has_percent"} <= set(flags)
    assert "duplicate_opening" in heuristic_flags(p, ok, Counter({"我只有三分钟直接说": 2}))


def test_risk_score_monotonic():
    assert risk_score(["leak"], 0) > risk_score([], 0)
    assert risk_score([], 9) > risk_score([], 1)


def test_apply_review_parse():
    import importlib.util
    import pathlib
    spec = importlib.util.spec_from_file_location("apply_review", pathlib.Path("scripts/apply_review.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    text = ("## 1. scn_001｜first_visit｜x\n- [x] 通过　[ ] 需修改　[ ] 剔除　　备注：\n"
            "## 2. scn_002｜x\n- [ ] 通过　[ ] 需修改　[x] 剔除　　备注：太配合\n"
            "## 3. scn_003｜x\n- [ ] 通过　[x] 需修改　[ ] 剔除　　备注：开场偏长\n"
            "## 4. scn_004｜x\n- [ ] 通过　[ ] 需修改　[ ] 剔除　　备注：\n")
    assert mod.parse(text) == {"scn_001": ("approved", ""), "scn_002": ("rejected", "太配合"),
                               "scn_003": ("needs_fix", "开场偏长")}
