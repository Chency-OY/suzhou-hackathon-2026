import pytest
from app.llm import load_prompt


def test_load_and_render_example():
    p = load_prompt("_example", "prompts")
    assert p.version == "0.1.0"
    assert "你好" in p.render(text="你好")


def test_missing_variable_raises():
    with pytest.raises(KeyError):
        load_prompt("_example", "prompts").render()


def test_front_matter_required(tmp_path):
    (tmp_path / "bad.md").write_text("没有 front matter", encoding="utf-8")
    with pytest.raises(ValueError):
        load_prompt("bad", tmp_path)
