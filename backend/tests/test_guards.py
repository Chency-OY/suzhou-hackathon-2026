from app.sessions.guards import has_question, norm_line, sanitize_signals, strip_event


def test_has_question():
    assert has_question("你这数据哪来的？")
    assert has_question("说明书上有写吗")
    assert has_question("（护士敲门递病历）你说什么？")
    assert not has_question("我现在用得挺好的，不用换。")
    assert not has_question("三分钟，说重点。")
    assert strip_event("（接电话）嗯，你说。") == "嗯，你说。"


def test_ignored_dropped_when_doctor_did_not_ask():
    out = sanitize_signals(["ignored_doctor_question", "relevant_to_concern"], "我现在用得挺好的，不用换。", None)
    assert out == ["relevant_to_concern"]


def test_ignored_kept_when_doctor_asked():
    assert "ignored_doctor_question" in sanitize_signals(["ignored_doctor_question"], "你这药副作用不小吧？", None)


def test_vague_dropped_when_there_is_substance():
    assert sanitize_signals(["relevant_to_concern", "vague_or_generic"], "x", None) == ["relevant_to_concern"]
    assert sanitize_signals(["vague_or_generic"], "x", None) == ["vague_or_generic"]


def test_evaded_boundary_after_compliance_bait():
    assert sanitize_signals([], "最近忙，改天一起吃个饭？", "benefit_bait") == ["evaded_boundary"]
    assert sanitize_signals(["relevant_to_concern"], "你们科室会能赞助吗？", "benefit_bait") == [
        "relevant_to_concern", "evaded_boundary"]
    assert sanitize_signals(["ignored_doctor_question"], "改天一起吃个饭？", "benefit_bait") == ["evaded_boundary"]


def test_not_evaded_when_rep_responded():
    for s in ("declined_boundary", "accepted_benefit", "promised_outcome", "disclosed_stat", "off_label_claim"):
        assert "evaded_boundary" not in sanitize_signals([s], "改天一起吃个饭？", "benefit_bait")


def test_non_compliance_bait_is_never_evaded():
    assert sanitize_signals([], "你们跟司美比怎么样？", "competitor_bash_bait") == []
    assert sanitize_signals([], "能保证有效吗？", "exaggeration_bait") == []
    assert sanitize_signals([], "你好", None) == []


def test_declined_and_accepted_keeps_the_violation():
    out = sanitize_signals(["declined_boundary", "accepted_benefit"], "改天吃个饭？", "benefit_bait")
    assert out == ["accepted_benefit"]


def test_norm_line_ignores_events_and_punctuation():
    assert norm_line("（接电话）三分钟，说重点。") == norm_line("三分钟说重点") == "三分钟说重点"
