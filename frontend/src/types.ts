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

export interface ProductPortfolioItem {
  id: string;
  name: string;
  generic_name: string;
  stage: "marketed" | "nda_review" | "pivotal";
  note: string;
  source_url: string;
  checked_on: string;
  verified: boolean;
}

export const SIGNALS = [
  "relevant_to_concern", "asked_open_question", "cited_evidence", "empathy_shown", "addressed_objection",
  "vague_or_generic", "pushy", "exaggeration", "off_label_claim", "competitor_bashing",
  "ignored_doctor_question", "proposed_next_step",
  "accepted_benefit", "disclosed_stat", "promised_outcome", "declined_boundary", "evaded_boundary",
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
  judge_note: string;
  judge_degraded: boolean;
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
  end_reason: EndReason | null; degraded: boolean; report_id?: string | null;
  judge_note: string; judge_degraded: boolean;
}
export interface FinishOut { session_id: string; ended: boolean; end_reason: EndReason | null; report_id: string | null }

export type ScoreDimension = "opening" | "discovery" | "product_evidence" | "objection_handling" | "closing" | "communication";
export interface ReportFinding {
  turn_idx: number;
  kind: "strength" | "issue" | "missed_opportunity" | "compliance_violation";
  dimension: ScoreDimension;
  quote: string;
  explanation: string;
  better_version: string | null;
}
export interface ReportView {
  id: string;
  session_id: string;
  dimension_scores: Record<ScoreDimension, number>;
  total_score: number;
  raw_total: number;
  capped_by_compliance: boolean;
  findings: ReportFinding[];
  summary: string;
  next_practice_tips: string[];
  scoring_mode: "model" | "unavailable";
  review_note: string;
  turns: TurnView[];
}

export interface TeamInfo {
  id: string;
  name: string;
  role: "owner" | "member";
  member_count: number;
  invite_code: string;
}
export interface TeamInsights {
  team_id: string;
  completed_sessions: number;
  scored_sessions: number;
  average_score: number | null;
  signal_counts: Record<string, number>;
}
export interface PlaybookCardView {
  id: string;
  title: string;
  situation: string;
  effective_response_pattern: string;
  example_lines: string[];
  status: "candidate" | "approved" | "rejected";
  scenario_id: string;
}

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

export interface ReviewEvidence { id: string; excerpt: string; source: string; url: string }
export interface ClaimFinding {
  claim: string;
  status: "possible_conflict" | "possible_support" | "insufficient" | "out_of_scope";
  grounded_in_raw: boolean;
  note: string;
  evidence_id: string;
  evidence_quote: string;
  candidates: ReviewEvidence[];
}
export interface DiaryReview {
  id: string;
  diary_id: string;
  owner_id: string;
  reviewed_at: string;
  policy_version: string;
  findings: ClaimFinding[];
  academic_candidate_count: number;
  academic_identity_confirmed: boolean;
}

export interface AcademicTension {
  diary_quote: string;
  source_id: string;
  source_quote: string;
  source_title: string;
  source_url: string;
  note: string;
}
export interface AcademicCrosscheck {
  id: string;
  diary_id: string;
  owner_id: string;
  radar_id: string;
  checked_at: string;
  policy_version: string;
  status: "compared" | "insufficient" | "no_radar";
  tensions: AcademicTension[];
  note: string;
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
  web_sources: RadarWebSource[];
  answer_points: RadarAnswerPoint[];
  web_status: "ok" | "unavailable" | "not_configured";
  radar_version: string;
  note: string;
  auto_refresh: boolean;
  last_auto_checked_at: string | null;
  refresh_error: string;
}

export interface RadarWebSource {
  id: string;
  kind: "paper" | "conference" | "talk";
  title: string;
  url: string;
  site_name: string;
  published_at: string;
  snippet: string;
  name_in_source: boolean;
  hospital_in_source: boolean;
  identity_status: "candidate";
}

export interface RadarAnswerPoint {
  kind: "paper" | "conference" | "talk";
  statement: string;
  source_id: string;
  evidence_quote: string;
}
