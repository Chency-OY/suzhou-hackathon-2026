import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { DifficultyBadge, Tag } from "../components/Badge";
import { useAsync } from "../hooks";
import { DEPT_LABEL, TYPE_LABEL } from "../labels";

const SESSION_ENABLED = import.meta.env.VITE_ENABLE_SESSION === "1";

export default function ScenarioDetailPage() {
  const { id = "" } = useParams();
  const nav = useNavigate();
  const { data, error, loading } = useAsync(() => api.getScenario(id), [id]);
  const [starting, setStarting] = useState(false);
  const [startErr, setStartErr] = useState<string | null>(null);

  async function start() {
    if (!data) return;
    setStarting(true);
    setStartErr(null);
    try {
      const out = await api.createSession(data.id);
      nav(`/session/${out.session_id}`);
    } catch (e) {
      setStartErr(e instanceof Error ? e.message : String(e));
      setStarting(false);
    }
  }

  if (loading) return <div className="game-panel p-10 text-center text-sm text-[#9bb7c6]">正在载入任务简报…</div>;
  if (error || !data) return <div className="game-alert">{error ?? "任务不存在"}　<Link className="game-link" to="/home">返回任务大厅</Link></div>;
  const p = data.persona_public;

  return (
    <div>
      <Link to="/home" className="game-link">← 返回任务大厅</Link>
      <div className="mt-6 flex flex-wrap items-end justify-between gap-4">
        <div><p className="game-kicker">MISSION BRIEF / 任务简报</p><h1 className="game-title mt-2 max-w-3xl">{data.rep_goal}</h1></div>
        <DifficultyBadge value={data.difficulty} />
      </div>
      <div className="mt-5 flex flex-wrap gap-2"><Tag>{data.program_id === "general" ? "通用沟通" : "信尔美资料"}</Tag><Tag>{DEPT_LABEL[data.department]}</Tag><Tag>{TYPE_LABEL[data.type]}</Tag></div>

      <div className="mt-6 grid gap-4 lg:grid-cols-[minmax(0,1fr)_290px]">
        <div className="game-panel p-6 sm:p-8">
          <section><h2 className="game-kicker">SITUATION / 拜访背景</h2><p className="mt-3 text-sm leading-8 text-[#d0e1e9]">{data.context_brief}</p></section>
          <section className="mt-8 border-t border-[#2b4b5e] pt-7"><h2 className="game-kicker">OBJECTIVES / 本次练习要点</h2><ol className="mt-4 space-y-4">{data.success_criteria.map((criterion, index) => <li key={criterion} className="flex gap-4 text-sm leading-7 text-[#c5d8e2]"><span className="grid h-7 w-7 shrink-0 place-items-center rounded border border-[#4d7e91] text-[10px] font-bold text-[#83dcec]">{String(index + 1).padStart(2, "0")}</span><span>{criterion}</span></li>)}</ol></section>
        </div>
        <aside className="game-panel h-fit p-5 sm:p-6">
          <h2 className="text-sm font-bold">模拟医生资料</h2>
          <div className="mt-4 space-y-0 text-xs"><div className="flex justify-between gap-3 border-b border-[#2b4b5e] py-3"><span className="text-[#91adbc]">职称</span><strong className="text-right font-semibold text-[#e8f5fa]">{p.title}</strong></div><div className="flex justify-between gap-3 border-b border-[#2b4b5e] py-3"><span className="text-[#91adbc]">医院层级</span><strong className="text-right font-semibold text-[#e8f5fa]">{p.hospital_tier}</strong></div><div className="flex justify-between gap-3 py-3"><span className="shrink-0 text-[#91adbc]">交流风格</span><strong className="text-right font-semibold leading-5 text-[#e8f5fa]">{p.style_hint}</strong></div></div>
          {startErr && <div className="game-alert mt-4">{startErr}</div>}
          <button type="button" onClick={() => void start()} disabled={!SESSION_ENABLED || starting} className="game-btn mt-5 w-full" title={SESSION_ENABLED ? "" : "演练功能即将开放"}>
            {!SESSION_ENABLED ? "暂未开放" : starting ? "正在进入…" : "开始任务"}<span aria-hidden="true">→</span>
          </button>
          <p className="mt-4 text-[11px] leading-5 text-[#8eacbc]">医生和情境均为合成。请勿输入真实患者或医生的个人信息。</p>
        </aside>
      </div>
    </div>
  );
}
