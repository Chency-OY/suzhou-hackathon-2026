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
  program_id: string;
  type: ScenarioType;
  persona_id: string;
  rep_goal: string;
  context_brief: string;
  opening_line: string;
  success_criteria: string[];
  source: "generated" | "playbook" | "curated";
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
  program?: string;
  dept?: Department;
  difficulty?: Difficulty;
  type?: ScenarioType;
}

export interface TrainingProgram {
  id: string;
  title: string;
  description: string;
  scope: "general" | "product";
}

export const SIGNALS = [
  "relevant_to_concern", "asked_open_question", "cited_evidence", "empathy_shown", "addressed_objection",
  "vague_or_generic", "pushy", "exaggeration", "off_label_claim", "competitor_bashing",
  "ignored_doctor_question", "proposed_next_step",
] as const;
export type Signal = (typeof SIGNALS)[number];

export const END_REASONS = ["agreed_next_step", "doctor_left", "time_up", "rep_ended"] as const;
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
  diary_id: string | null;
  rehearsal_note: string;
  turns: TurnView[];
}

export interface SessionSummary {
  id: string;
  scenario_id: string;
  started_at: string;
  ended_at: string | null;
  end_reason: EndReason | null;
  rep_turns: number;
}

export interface CreateSessionOut { session_id: string; opening_line: string; doctor_state: DoctorState }
export interface TurnOut {
  doctor_reply: string; doctor_state: DoctorState; signals: Signal[]; ended: boolean;
  end_reason: EndReason | null; degraded: boolean;
}
export interface FinishOut { session_id: string; ended: boolean; end_reason: EndReason | null; report_id: string | null }

export interface DiaryDigest {
  summary: string;
  first_impressions: string[];
  doctor_feedback: string[];
  what_to_improve: string[];
  next_visit: string[];
  uncertain_claims: string[];
}

export interface FieldDiary {
  id: string;
  owner_id: string;
  created_at: string;
  hospital: string;
  doctor_name: string;
  raw_text: string;
  digest: DiaryDigest;
  degraded: boolean;
  review_status: string;
}

export interface AcademicWork {
  id: string;
  title: string;
  publication_date: string;
  journal: string;
  author_name: string;
  affiliation: string;
  url: string;
  doi: string;
  identity_status: "candidate" | "confirmed";
}

export interface AcademicRadar {
  id: string;
  owner_id: string;
  doctor_name: string;
  hospital: string;
  searched_at: string;
  institution_name: string;
  institution_url: string;
  search_name: string;
  status: "found" | "no_match" | "ambiguous_institution";
  works: AcademicWork[];
  note: string;
}
