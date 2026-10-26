import { Link } from "react-router-dom";
import { api } from "../api";
import { useAsync } from "../hooks";
import { END_REASON_LABEL, TYPE_LABEL } from "../labels";

export default function SessionHistoryPage() {
  const { data, error, loading } = useAsync(async () => {
    const [sessions, scenarios] = await Promise.all([api.listSessions(), api.listScenarios({})]);
    return {
      sessions,
      scenarios: new Map(scenarios.map((x) => [x.id, x])),
    };
  }, []);

  return <div className="mx-auto max-w-5xl">
    <p className="game-kicker">TRAINING ARCHIVE / 练习档案</p>
    <h1 className="game-title mt-2">回看每一次对话</h1>
    <p className="game-muted mt-3 max-w-2xl text-sm leading-7">这里列出当前账号的练习记录。换设备登录同一账号，也能继续查看。</p>
    {loading && <div className="game-panel mt-6 p-10 text-center text-sm text-[#a1bbca]">正在读取练习档案…</div>}
    {error && <div className="game-alert mt-6">{error}</div>}
    {data?.sessions.length === 0 && <div className="game-panel mt-7 p-10 text-center"><div className="game-kicker">NO RECORDS</div><p className="mt-3 text-sm text-[#c4d9e3]">还没有练习记录</p><Link to="/home" className="game-btn mt-5">前往任务大厅 →</Link></div>}
    {data && data.sessions.length > 0 && <div className="mt-7 space-y-3">{data.sessions.map((session, index) => {
      const scenario = data.scenarios.get(session.scenario_id);
      const repTurns = session.rep_turns;
      return <Link key={session.id} to={session.ended_at ? `/review/${session.id}` : `/session/${session.id}`} className="game-card flex flex-wrap items-center gap-4 p-5 no-underline">
        <div className="grid h-10 w-10 shrink-0 place-items-center rounded-md border border-[#43738a] text-xs font-bold text-[#84d9eb]">{String(index + 1).padStart(2, "0")}</div>
        <div className="min-w-[220px] flex-1"><h2 className="text-sm font-bold leading-6 text-[#eff7fb]">{scenario ? `${TYPE_LABEL[scenario.type]} · ${scenario.rep_goal}` : "已归档情境"}</h2><div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-[#99b6c5]"><span>{new Date(session.started_at).toLocaleString("zh-CN")}</span><span>{repTurns} 次发言</span><span>{session.end_reason ? END_REASON_LABEL[session.end_reason] : "进行中"}</span></div></div>
        <span className="game-link shrink-0">{session.ended_at ? "查看复盘 →" : "继续演练 →"}</span>
      </Link>;
    })}</div>}
  </div>;
}
