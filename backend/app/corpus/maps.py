"""骨架编号到类型、陷阱、结局的映射（集中放这里，生成器和对话引擎共用）。"""

SKELETON_TYPE = {
    "S01": "first_visit", "S02": "second_visit", "S03": "third_visit",
    "S04": "hard_refusal", "S05": "hard_refusal", "S06": "hard_refusal",
    "S07": "soft_refusal", "S08": "safety_concern", "S09": "competitor_compare",
    "S10": "turnover", "S11": "empty_handed", "S12": "compliance_bait",
    "S13": "off_label_bait", "S14": "followup_visit",
}

# 陷阱属于场景，不属于画像：同一个医生在不同场景里抛出的难题不同
SKELETON_BAITS = {
    "S03": ["exaggeration_bait"],
    "S09": ["competitor_bash_bait"],
    "S12": ["benefit_bait", "stat_bait", "promise_bait"],
    "S13": ["off_label_bait"],
}

# 回合用尽时的真实结局（缺省按信任度判断）
SKELETON_END = {"S05": "materials_left", "S06": "referred", "S07": "soft_decline"}

BAIT_INTENT = {
    "off_label_bait": "bait_off_label",
    "competitor_bash_bait": "bait_competitor",
    "exaggeration_bait": "bait_exaggeration",
    "benefit_bait": "bait_benefit",
    "stat_bait": "bait_stat",
    "promise_bait": "bait_promise",
}
