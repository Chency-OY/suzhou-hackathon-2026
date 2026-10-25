import type { Department, Difficulty, ScenarioType } from "./types";

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
