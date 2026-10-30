import type { Department, Difficulty, ScenarioType, EndReason, Signal } from "./types";

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
  off_label_bait: "合规考验",
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
};

export const SIGNAL_POLARITY: Record<Signal, "good" | "bad"> = {
  relevant_to_concern: "good", asked_open_question: "good", cited_evidence: "good", empathy_shown: "good",
  addressed_objection: "good", proposed_next_step: "good",
  vague_or_generic: "bad", pushy: "bad", exaggeration: "bad", off_label_claim: "bad",
  competitor_bashing: "bad", ignored_doctor_question: "bad",
};

export const END_REASON_LABEL: Record<EndReason, string> = {
  agreed_next_step: "医生同意了你提出的下一步",
  doctor_left: "医生失去耐心，结束了对话",
  time_up: "拜访时间已到",
  rep_ended: "你主动结束了演练",
};
