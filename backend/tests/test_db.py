from app.db import Repo
from app.models import DoctorPersona, Scenario, Session

from tests.factories import make_persona, make_scenario, make_session


def test_roundtrip_and_upsert(tmp_path):
    repo = Repo(f"sqlite:///{tmp_path}/t.db")
    p = make_persona()
    repo.save(p)
    assert repo.get(DoctorPersona, p.id) == p
    repo.save(make_persona(current_habit="已更新"))      # 同 id 覆盖
    assert repo.get(DoctorPersona, p.id).current_habit == "已更新"
    assert len(repo.list(DoctorPersona)) == 1


def test_session_with_turns_roundtrip(tmp_path):
    repo = Repo(f"sqlite:///{tmp_path}/t.db")
    s = make_session()
    repo.save(s)
    got = repo.get(Session, s.id)
    assert got == s and got.turns[1].signals == ["asked_open_question"]


def test_kinds_are_isolated_and_delete(tmp_path):
    repo = Repo(f"sqlite:///{tmp_path}/t.db")
    repo.save(make_persona())
    repo.save(make_scenario())
    assert len(repo.list(DoctorPersona)) == 1 and len(repo.list(Scenario)) == 1
    assert repo.delete(Scenario, "scn_001") is True
    assert repo.delete(Scenario, "scn_001") is False
    assert repo.get(Scenario, "scn_001") is None
