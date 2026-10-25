import type { ScenarioDetail, ScenarioFilters, ScenarioItem } from "./types";

export function buildQuery(params: Record<string, string | undefined>): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v) q.set(k, v);
  }
  const s = q.toString();
  return s ? `?${s}` : "";
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`/api${path}`);
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

export const api = {
  listScenarios: (f: ScenarioFilters) =>
    get<ScenarioItem[]>(`/scenarios${buildQuery({ dept: f.dept, difficulty: f.difficulty, type: f.type })}`),
  getScenario: (id: string) => get<ScenarioDetail>(`/scenarios/${encodeURIComponent(id)}`),
};
