import type {
  AcademicRadar, CreateSessionOut, DiaryReview, FieldDiary, FinishOut, ReportView, ScenarioDetail, ScenarioFilters, ScenarioItem, SessionSummary, SessionView, TeamInfo, TeamInsights, TrainingProgram, TurnOut,
} from "./types";

export function buildQuery(params: Record<string, string | undefined>): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v) q.set(k, v);
  }
  const s = q.toString();
  return s ? `?${s}` : "";
}

async function parse<T>(r: Response): Promise<T> {
  if (!r.ok) {
    let msg = `请求失败（${r.status}）`;
    try {
      const j = await r.json();
      msg = j?.detail?.error?.message ?? j?.error?.message ?? msg;
    } catch {
      /* 非 JSON 响应，保留默认信息 */
    }
    throw new Error(msg);
  }
  return (await r.json()) as T;
}

export const apiUrl = (path: string, base = import.meta.env.BASE_URL) => `${base}api${path}`;

const get = <T>(path: string) => fetch(apiUrl(path), { credentials: "same-origin" }).then((r) => parse<T>(r));
const post = <T>(path: string, body?: unknown) =>
  fetch(apiUrl(path), {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  }).then((r) => parse<T>(r));

export const api = {
  listPrograms: () => get<TrainingProgram[]>("/programs"),
  listScenarios: (f: ScenarioFilters) =>
    get<ScenarioItem[]>(`/scenarios${buildQuery({ program: f.program, dept: f.dept, difficulty: f.difficulty, type: f.type })}`),
  getScenario: (id: string) => get<ScenarioDetail>(`/scenarios/${encodeURIComponent(id)}`),
  createSession: (scenarioId: string, diaryId?: string | null) =>
    post<CreateSessionOut>("/sessions", { scenario_id: scenarioId, diary_id: diaryId || null }),
  listSessions: () => get<SessionSummary[]>("/sessions"),
  getSession: (id: string) => get<SessionView>(`/sessions/${encodeURIComponent(id)}`),
  getReport: (id: string) => get<ReportView>(`/reports/${encodeURIComponent(id)}`),
  sendTurn: (id: string, text: string) => post<TurnOut>(`/sessions/${encodeURIComponent(id)}/turns`, { text }),
  finishSession: (id: string) => post<FinishOut>(`/sessions/${encodeURIComponent(id)}/finish`),
  listDiary: () => get<FieldDiary[]>("/diary"),
  createDiary: (body: { hospital: string; doctor_name: string; raw_text: string }) => post<FieldDiary>("/diary", body),
  reviewDiary: (id: string) => post<DiaryReview>(`/diary/${encodeURIComponent(id)}/review`),
  deleteDiary: (id: string) => fetch(apiUrl(`/diary/${encodeURIComponent(id)}`), {
    method: "DELETE", credentials: "same-origin",
  }).then((response) => parse<{ ok: boolean }>(response)),
  listRadar: () => get<AcademicRadar[]>("/radar"),
  searchRadar: (doctorName: string, hospital: string, refresh = false) =>
    post<AcademicRadar>("/radar/search", { doctor_name: doctorName, hospital, refresh }),
  getTeam: () => get<TeamInfo>("/team"),
  createTeam: (name: string) => post<TeamInfo>("/team", { name }),
  joinTeam: (inviteCode: string) => post<TeamInfo>("/team/join", { invite_code: inviteCode }),
  rotateTeamInvite: () => post<TeamInfo>("/team/invite"),
  leaveTeam: () => post<{ ok: boolean }>("/team/leave"),
  getTeamInsights: () => get<TeamInsights>("/team/insights"),
};
