import pytest
from app.models import DoctorState, Finding, Report
from pydantic import ValidationError

from tests.factories import make_persona, make_session


def test_persona_bounds():
    with pytest.raises(ValidationError):
        make_persona(time_budget_turns=2)
    with pytest.raises(ValidationError):
        make_persona(initial_trust=101)
    with pytest.raises(ValidationError):
        make_persona(concerns=[])


def test_state_clamps_on_init_and_assignment():
    s = DoctorState(trust=150, patience=-5, engagement=50)
    assert (s.trust, s.patience) == (100, 0)
    s.trust += 200
    assert s.trust == 100
    s.engagement -= 999
    assert s.engagement == 0


def test_report_rejects_bad_scores():
    with pytest.raises(ValidationError):
        Report(id="r", session_id="s", dimension_scores={"opening": 11}, total_score=10, raw_total=10)
    with pytest.raises(ValidationError):
        Report(id="r", session_id="s", dimension_scores={"nope": 1}, total_score=1, raw_total=1)


def test_report_drops_hallucinated_quotes():
    sess = make_session()
    good = Finding(turn_idx=1, kind="strength", dimension="discovery", quote="了解一下您门诊肥胖患者",
                   explanation="开放式提问")
    bad = Finding(turn_idx=1, kind="issue", dimension="closing", quote="这句话原文里没有", explanation="x")
    oob = Finding(turn_idx=99, kind="issue", dimension="closing", quote="任意", explanation="x")
    rep = Report(id="r", session_id="s", dimension_scores={"discovery": 15}, total_score=15, raw_total=15,
                 findings=[good, bad, oob])
    new, dropped = rep.drop_invalid_findings(sess.turns)
    assert dropped == 2 and len(new.findings) == 1 and new.findings[0].quote == good.quote
