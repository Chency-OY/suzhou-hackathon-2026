DIMENSIONS = (
    "opening",             # 开场与目标设定
    "discovery",           # 需求探寻
    "product_evidence",    # 产品信息与证据运用
    "objection_handling",  # 异议处理
    "closing",             # 促成与下一步
    "communication",       # 沟通表达
)

DIMENSION_WEIGHTS = {
    "opening": 10,
    "discovery": 20,
    "product_evidence": 25,
    "objection_handling": 20,
    "closing": 10,
    "communication": 15,
}

DIMENSION_LABELS = {
    "opening": "开场与目标设定",
    "discovery": "需求探寻",
    "product_evidence": "产品信息与证据运用",
    "objection_handling": "异议处理",
    "closing": "促成与下一步",
    "communication": "沟通表达",
}

SIGNALS = (
    "relevant_to_concern", "asked_open_question", "cited_evidence", "empathy_shown",
    "addressed_objection", "vague_or_generic", "pushy", "exaggeration",
    "off_label_claim", "competitor_bashing", "ignored_doctor_question", "proposed_next_step",
    "accepted_benefit", "disclosed_stat", "promised_outcome",
)

assert sum(DIMENSION_WEIGHTS.values()) == 100
