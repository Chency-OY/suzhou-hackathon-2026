export const DEPARTMENTS = ["endocrinology", "cardiology", "hepatology"] as const;
export const DIFFICULTIES = ["easy", "normal", "hard"] as const;
export const SCENARIO_TYPES = [
  "first_visit", "post_conference", "safety_concern", "competitor_compare",
  "time_pressure", "revisit_after_rejection", "off_label_bait",
] as const;

export type Department = (typeof DEPARTMENTS)[number];
export type Difficulty = (typeof DIFFICULTIES)[number];
export type ScenarioType = (typeof SCENARIO_TYPES)[number];

export interface ScenarioItem {
  id: string;
  type: ScenarioType;
  persona_id: string;
  rep_goal: string;
  context_brief: string;
  opening_line: string;
  success_criteria: string[];
  source: "generated" | "playbook";
  department: Department;
  difficulty: Difficulty;
}

export interface PersonaPublic {
  department: Department;
  title: string;
  hospital_tier: string;
  style_hint: string;
  difficulty: Difficulty;
}

export interface ScenarioDetail extends ScenarioItem {
  persona_public: PersonaPublic;
}

export interface ScenarioFilters {
  dept?: Department;
  difficulty?: Difficulty;
  type?: ScenarioType;
}
