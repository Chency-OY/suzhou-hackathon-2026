export const DEPARTMENTS = ["endocrinology", "cardiology", "hepatology"] as const;
export const DIFFICULTIES = ["easy", "normal", "hard"] as const;
export const SCENARIO_TYPES = [
  "first_visit", "post_conference", "safety_concern", "competitor_compare",
  "time_pressure", "revisit_after_rejection", "off_label_bait",
  "second_visit", "third_visit", "hard_refusal", "soft_refusal", "turnover", "empty_handed",
  "compliance_bait", "followup_visit",
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
  skeleton_id: string | null;
  setting: Record<string, string>;
  pre_info: string;
  hard_gate: boolean;
  post_task: string | null;
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

export const SIGNALS = [
  "relevant_to_concern", "asked_open_question", "cited_evidence", "empathy_shown", "addressed_objection",
  "vague_or_generic", "pushy", "exaggeration", "off_label_claim", "competitor_bashing",
  "ignored_doctor_question", "proposed_next_step",   "accepted_benefit", "disclosed_stat", "promised_outcome",
  "declined_boundary", "evaded_boundary",
] as const;
export type Signal = (typeof SIGNALS)[number];

export const END_REASONS = [
  "agreed_next_step", "doctor_left", "time_up", "rep_ended", "materials_left", "referred", "soft_decline",
] as const;
export type EndReason = (typeof END_REASONS)[number];

export interface DoctorState {
  trust: number;
  patience: number;
  engagement: number;
  revealed_hidden_objection: boolean;
}

export interface TurnView {
  idx: number;
  speaker: "rep" | "doctor";
  text: string;
  signals: Signal[];
  state_after: DoctorState | null;
}

export interface SessionView {
  id: string;
  scenario_id: string;
  rep_id: string;
  started_at: string;
  ended_at: string | null;
  end_reason: EndReason | null;
  pre_goal: string | null;
  visit_note: string | null;
  turns: TurnView[];
}

export interface CreateSessionOut { session_id: string; opening_line: string; doctor_state: DoctorState }
export interface TurnOut {
  doctor_reply: string; doctor_state: DoctorState; signals: Signal[]; ended: boolean;
  end_reason: EndReason | null; degraded: boolean;
}
export interface FinishOut { session_id: string; ended: boolean; end_reason: EndReason | null; report_id: string | null }
