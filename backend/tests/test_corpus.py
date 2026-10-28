from app.corpus import load_bank, validate_bank
from app.corpus.maps import SKELETON_TYPE


def test_bank_loads_and_is_valid():
    bank = load_bank()
    assert [s.id for s in bank.scene_skeletons] == [f"S{i:02d}" for i in range(1, 15)]
    assert validate_bank(bank) == []
    assert set(SKELETON_TYPE) == {s.id for s in bank.scene_skeletons}


def test_utterance_helpers():
    bank = load_bank()
    assert len(bank.lines("soft_refusal")) == 10 and len(bank.lines("hard_refusal")) >= 5
    assert bank.lines("pressure_and_interrupt")
    assert bank.closing("followup_set") and bank.closing("hard_decline")
    assert bank.skeleton("S12").hard_gate is True


def test_validate_catches_percent():
    bank = load_bank()
    bad_sk = bank.scene_skeletons[0].model_copy(update={"rep_goal": "提升 30% 的效果"})
    bad = bank.model_copy(update={"scene_skeletons": [bad_sk, *bank.scene_skeletons[1:]]})
    assert any("百分比" in e for e in validate_bank(bad))
