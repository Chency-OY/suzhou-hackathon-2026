import type { Department, Difficulty, EndReason, ScenarioType, Signal } from "./types";

export const DEPT_LABEL: Record<Department, string> = {
  endocrinology: "内分泌科",
  cardiology: "心血管内科",
  hepatology: "消化/肝病科",
};

export const DIFFICULTY_LABEL: Record<Difficulty, string> = {
  easy: "友好开放",
  normal: "中性务实",
  hard: "质疑挑战",
};

export const DIFFICULTY_STYLE: Record<Difficulty, string> = {
  easy: "bg-emerald-100 text-emerald-800",
  normal: "bg-amber-100 text-amber-800",
  hard: "bg-rose-100 text-rose-800",
};

export const TYPE_LABEL: Record<ScenarioType, string> = {
  first_visit: "首次拜访",
  post_conference: "学术会后跟进",
  safety_concern: "安全性顾虑",
  competitor_compare: "竞品对比",
  time_pressure: "时间紧张",
  revisit_after_rejection: "被拒后再拜访",
  off_label_bait: "超适应症追问",
  second_visit: "二访",
  third_visit: "三访",
  hard_refusal: "硬拒绝",
  soft_refusal: "温柔拒绝",
  turnover: "换人后的信任",
  empty_handed: "空手拜访",
  compliance_bait: "合规考验",
  followup_visit: "复访跟进",
};

export const SIGNAL_LABEL: Record<Signal, string> = {
  relevant_to_concern: "切中关注点",
  asked_open_question: "开放式提问",
  cited_evidence: "引用证据",
  empathy_shown: "表达理解",
  addressed_objection: "回应异议",
  vague_or_generic: "空泛套话",
  pushy: "催促施压",
  exaggeration: "夸大表述",
  off_label_claim: "疑似超适应症",
  competitor_bashing: "贬低竞品",
  ignored_doctor_question: "回避提问",
  proposed_next_step: "提出下一步",
  accepted_benefit: "接了利益试探",
  disclosed_stat: "涉及处方量",
  promised_outcome: "承诺销售结果",
};

export const SIGNAL_POLARITY: Record<Signal, "good" | "bad"> = {
  relevant_to_concern: "good", asked_open_question: "good", cited_evidence: "good", empathy_shown: "good",
  addressed_objection: "good", proposed_next_step: "good",
  vague_or_generic: "bad", pushy: "bad", exaggeration: "bad", off_label_claim: "bad",
  competitor_bashing: "bad", ignored_doctor_question: "bad",
  accepted_benefit: "bad", disclosed_stat: "bad", promised_outcome: "bad",
};

export const END_REASON_LABEL: Record<EndReason, string> = {
  agreed_next_step: "医生同意了你提出的下一步",
  doctor_left: "医生失去耐心，结束了对话",
  time_up: "拜访时间已到",
  rep_ended: "你主动结束了演练",
  materials_left: "医生留下了资料，等你回访",
  referred: "医生把你转介给了别人",
  soft_decline: "医生客气地收了场",
};
