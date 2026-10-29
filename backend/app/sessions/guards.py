"""对裁判输出做确定性清洗：模型常见的误判，用规则兜住。"""
from __future__ import annotations

import re

QUESTION_HINT = re.compile(r"[？?]|吗|呢|什么|怎么|为什么|哪|多少|能不能|是不是|有没有|行不行|可不可以")
SUPPORT = {"relevant_to_concern", "cited_evidence", "addressed_objection", "proposed_next_step",
           "asked_open_question"}
COMPLIANCE_BAITS = {"off_label_bait", "benefit_bait", "stat_bait", "promise_bait"}
# 代表对合规试探"有所回应"的信号：有这些之一，就不算回避
RESPONSES = {"declined_boundary", "accepted_benefit", "disclosed_stat", "promised_outcome",
             "off_label_claim", "exaggeration"}


def strip_event(text: str) -> str:
    """去掉医生台词开头的环境事件，如「（护士敲门递病历）」。"""
    return re.sub(r"^（[^）]*）", "", text).strip()


def norm_line(text: str) -> str:
    """台词比较用：去掉环境事件、标点和空白。"""
    return re.sub(r"[\s，。,.、；;：:！!？?（）()“”\"'‘’\-—]+", "", strip_event(text))


def has_question(text: str) -> bool:
    return bool(QUESTION_HINT.search(strip_event(text)))


def sanitize_signals(signals: list[str], last_doctor_text: str, last_bait: str | None) -> list[str]:
    sig = list(dict.fromkeys(signals))
    # 1. 医生上一句不是提问，就不可能"回避提问"
    if "ignored_doctor_question" in sig and not has_question(last_doctor_text):
        sig.remove("ignored_doctor_question")
    # 2. 已经有实质内容的回应，就不算空泛
    if "vague_or_generic" in sig and set(sig) & SUPPORT:
        sig.remove("vague_or_generic")
    # 3. 又拒绝又接受：合规上宁严勿宽，保留违规，去掉"拒绝"
    if "declined_boundary" in sig and "accepted_benefit" in sig:
        sig.remove("declined_boundary")
    # 4. 医生上一句抛了合规试探，代表既没明确拒绝、也没任何回应 → 回避边界（替代"回避提问"，避免重复扣分）
    if last_bait in COMPLIANCE_BAITS and not (set(sig) & RESPONSES):
        sig = [s for s in sig if s != "ignored_doctor_question"]
        sig.append("evaded_boundary")
    return sig
