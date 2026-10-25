import sys

sys.path.insert(0, "backend")
from app.rag.facts import load_facts


def test_load_facts_valid_and_errors(tmp_path):
    p = tmp_path / "facts.yaml"
    p.write_text(
        "- {id: a1, category: efficacy, statement: '某研究显示体重下降', verified: true}\n"
        "- {id: a1, category: efficacy, statement: '重复 id 的条目内容'}\n"
        "- {id: a2, category: safety}\n"
        "- {id: a3, category: access, statement: '医保相关说明条目'}\n",
        encoding="utf-8",
    )
    facts, errors = load_facts(p)
    assert [f.id for f in facts] == ["a1", "a3"]
    assert any("重复 id" in e for e in errors) and any("无效" in e for e in errors)
    assert facts[0].verified is True and facts[1].verified is False


def test_load_facts_dict_wrapper(tmp_path):
    p = tmp_path / "facts.yaml"
    p.write_text("facts:\n  - {id: x1, category: company, statement: '公司背景相关条目'}\n", encoding="utf-8")
    facts, errors = load_facts(p)
    assert len(facts) == 1 and not errors
