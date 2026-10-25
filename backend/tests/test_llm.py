import pytest
from app.llm import BudgetExceeded, MockLLM, UsageTracker, extract_json, structured_call
from pydantic import BaseModel


class Out(BaseModel):
    ok: bool
    n: int


FALLBACK = Out(ok=False, n=-1)
MSG = [{"role": "user", "content": "hi"}]


def run(mock, **kw):
    return structured_call(mock, prompt_name="p", system="s", messages=MSG, model_cls=Out,
                           fallback=kw.pop("fallback", FALLBACK), **kw)


def test_valid_json():
    out, degraded = run(MockLLM({"p": '{"ok": true, "n": 1}'}))
    assert out == Out(ok=True, n=1) and degraded is False


def test_fenced_and_chatty_output():
    fence = "`" * 3
    out, degraded = run(MockLLM({"p": f'好的：\n{fence}json\n{{"ok": true, "n": 2}}\n{fence}\n谢谢'}))
    assert out.n == 2 and degraded is False


def test_retry_then_success():
    mock = MockLLM({"p": ["not json", '{"ok": true, "n": 3}']})
    out, degraded = run(mock)
    assert out.n == 3 and degraded is False
    assert len(mock.calls) == 2
    assert "无法解析" in mock.calls[1]["messages"][-1]["content"]   # 纠错提示已追加


def test_schema_violation_retries_then_falls_back():
    mock = MockLLM({"p": '{"ok": "maybe", "n": "x"}'})
    out, degraded = run(mock, max_retries=2)
    assert out == FALLBACK and degraded is True
    assert len(mock.calls) == 3


def test_callable_fallback():
    out, degraded = run(MockLLM({"p": "garbage"}), fallback=lambda: Out(ok=False, n=0), max_retries=0)
    assert degraded is True and out.n == 0


def test_extract_json_handles_braces_in_strings():
    assert extract_json('x {"a": "}{", "b": [1, {"c": 2}]} y') == '{"a": "}{", "b": [1, {"c": 2}]}'


def test_budget_guard_blocks_calls():
    tracker = UsageTracker(daily_cap=10)
    mock = MockLLM({"p": '{"ok": true, "n": 1}'}, tracker=tracker)
    tracker.record("seed", 8, 8)               # 已用 16 >= 10
    with pytest.raises(BudgetExceeded):
        run(mock)
    assert mock.calls == []                    # 超限时不应发起调用


def test_usage_recorded_and_persisted(tmp_path):
    tracker = UsageTracker(log_dir=tmp_path, daily_cap=0)
    mock = MockLLM({"p": '{"ok": true, "n": 1}'}, tracker=tracker)
    run(mock)
    assert tracker.summary()["p"]["calls"] == 1 and tracker.today_total > 0
    reloaded = UsageTracker(log_dir=tmp_path)   # 重启后可恢复当日累计
    assert reloaded.today_total == tracker.today_total
