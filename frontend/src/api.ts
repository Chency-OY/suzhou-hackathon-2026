import type {
  CreateSessionOut, FinishOut, ScenarioDetail, ScenarioFilters, ScenarioItem, SessionView, TrainingProgram, TurnOut,
} from "./types";
import { authorizationHeader } from "./auth";

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

const get = <T>(path: string) => fetch(apiUrl(path), { headers: authorizationHeader() }).then((r) => parse<T>(r));
const post = <T>(path: string, body?: unknown) =>
  fetch(apiUrl(path), {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authorizationHeader() },
    body: body === undefined ? undefined : JSON.stringify(body),
  }).then((r) => parse<T>(r));

export const api = {
  listPrograms: () => get<TrainingProgram[]>("/programs"),
  listScenarios: (f: ScenarioFilters) =>
    get<ScenarioItem[]>(`/scenarios${buildQuery({ program: f.program, dept: f.dept, difficulty: f.difficulty, type: f.type })}`),
  getScenario: (id: string) => get<ScenarioDetail>(`/scenarios/${encodeURIComponent(id)}`),
  createSession: (scenarioId: string, repId: string) =>
    post<CreateSessionOut>("/sessions", { scenario_id: scenarioId, rep_id: repId }),
  getSession: (id: string) => get<SessionView>(`/sessions/${encodeURIComponent(id)}`),
  sendTurn: (id: string, text: string) => post<TurnOut>(`/sessions/${encodeURIComponent(id)}/turns`, { text }),
  finishSession: (id: string) => post<FinishOut>(`/sessions/${encodeURIComponent(id)}/finish`),
};
