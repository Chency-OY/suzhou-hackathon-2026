import { Link } from "react-router-dom";
import { api } from "../api";
import { useAsync } from "../hooks";
import { END_REASON_LABEL, TYPE_LABEL } from "../labels";
import { readSessionIds } from "../lib/rep";

export default function SessionHistoryPage() {
  const { data, error, loading } = useAsync(async () => {
    const ids = readSessionIds().slice(0, 30);
    const [sessions, scenarios] = await Promise.all([
      Promise.allSettled(ids.map((id) => api.getSession(id))),
      api.listScenarios({}),
    ]);
    return {
      sessions: sessions.filter((x): x is PromiseFulfilledResult<Awaited<ReturnType<typeof api.getSession>>> => x.status === "fulfilled")
        .map((x) => x.value).sort((a, b) => b.started_at.localeCompare(a.started_at)),
      scenarios: new Map(scenarios.map((x) => [x.id, x])),
    };
  }, []);

  return <div className="mx-auto max-w-4xl">
    <h1 className="text-2xl font-semibold text-slate-900">我的练习记录</h1>
    <p className="mt-2 text-sm leading-6 text-slate-600">服务端保存对话；此处的记录索引只保存在当前浏览器。更换设备或清除浏览器数据后，这里不会再显示以前的练习。</p>
    {loading && <p className="py-12 text-center text-sm text-slate-500">正在加载记录…</p>}
    {error && <p className="mt-5 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</p>}
    {data?.sessions.length === 0 && <div className="mt-7 rounded-xl border border-slate-200 bg-white p-8 text-center">
      <p className="text-slate-700">还没有练习记录</p>
      <Link to="/home" className="mt-4 inline-block rounded-md bg-slate-900 px-4 py-2 text-sm text-white">选择情境开始练习</Link>
    </div>}
    {data && data.sessions.length > 0 && <div className="mt-6 space-y-3">
      {data.sessions.map((session) => {
        const scenario = data.scenarios.get(session.scenario_id);
        const repTurns = session.turns.filter((turn) => turn.speaker === "rep").length;
        return <Link key={session.id} to={session.ended_at ? `/review/${session.id}` : `/session/${session.id}`}
          className="block rounded-xl border border-slate-200 bg-white p-5 transition hover:border-teal-600 hover:shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <h2 className="font-semibold leading-6 text-slate-900">{scenario ? `${TYPE_LABEL[scenario.type]} · ${scenario.rep_goal}` : "已归档情境"}</h2>
            <span className="shrink-0 text-xs text-teal-700">{session.ended_at ? "查看复盘 →" : "继续演练 →"}</span>
          </div>
          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
            <span>{new Date(session.started_at).toLocaleString("zh-CN")}</span>
            <span>{repTurns} 次发言</span>
            <span>{session.end_reason ? END_REASON_LABEL[session.end_reason] : "进行中"}</span>
          </div>
        </Link>;
      })}
    </div>}
  </div>;
}
