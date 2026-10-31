import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { DifficultyBadge, Tag } from "../components/Badge";
import { useAsync } from "../hooks";
import { DEPT_LABEL, DIFFICULTY_LABEL, TYPE_LABEL } from "../labels";
import {
  DEPARTMENTS, DIFFICULTIES, SCENARIO_TYPES,
  type Department, type Difficulty, type ScenarioFilters, type ScenarioType,
} from "../types";

const SESSION_ENABLED = import.meta.env.VITE_ENABLE_SESSION === "1";

function FilterSelect({ label, value, options, onChange }: {
  label: string; value: string; options: { value: string; label: string }[]; onChange: (v: string) => void;
}) {
  return (
    <label className="min-w-[136px] flex-1 text-[11px] font-bold text-[#92b1c3]">
      <span className="mb-1.5 block">{label}</span>
      <select className="game-field" value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">全部</option>
        {options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
      </select>
    </label>
  );
}

export default function ScenarioListPage() {
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const diaryId = searchParams.get("diary");
  const [filters, setFilters] = useState<ScenarioFilters>({ program: searchParams.get("program") === "xinermei" ? "xinermei" : "general" });
  const [startingId, setStartingId] = useState<string | null>(null);
  const [startError, setStartError] = useState<string | null>(null);
  const programs = useAsync(() => api.listPrograms(), []);
  const { data, error, loading } = useAsync(
    () => api.listScenarios(filters),
    [filters.program, filters.dept, filters.difficulty, filters.type],
  );

  async function start(id: string) {
    if (!SESSION_ENABLED || startingId) return;
    setStartingId(id);
    setStartError(null);
    try {
      const out = await api.createSession(id, diaryId);
      nav(`/session/${out.session_id}`);
    } catch (e) {
      setStartError(e instanceof Error ? e.message : String(e));
      setStartingId(null);
    }
  }

  return (
    <div>
      {diaryId && <div className="game-alert mb-5" role="status">这次会把你日记中的沟通感受作为虚构演练线索。医学说法不会进入角色设定。<Link className="game-link ml-2" to="/diary">返回日记</Link></div>}
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_290px]">
        <section className="sim-home-hero">
          <div className="sim-home-copy"><p className="sim-eyebrow">FRONTLINE LAB <span>·</span> AI 沟通训练</p><h1>把每一次拜访，<br /><em>先练到心里有数。</em></h1><p>走进虚构医生的诊室，直接说出你的回答。DeepSeek 接住每一句话，模拟追问，并给出逐轮沟通判断。</p><div className="sim-home-steps"><span>01 选情境</span><b>→</b><span>02 说出来</span><b>→</b><span>03 看判断</span></div><a className="sim-home-download" href={`${import.meta.env.BASE_URL}rep-trainer.apk`} download="rep-trainer.apk"><img src={`${import.meta.env.BASE_URL}app-icon.svg?v=3`} width="26" height="26" alt="" /><span>下载安卓 App</span><b aria-hidden="true">↗</b></a><small className="sim-home-download-hint">安卓手机用浏览器下载后安装 · 当前版本支持语音输入</small></div>
          <div className="sim-home-preview" aria-hidden="true"><div className="sim-preview-top"><i /> LIVE SESSION <span>● AI ONLINE</span></div><div className="sim-preview-doctor"><small>模拟医生</small><p>你说这个方案更合适，依据是什么？</p></div><div className="sim-preview-rep"><small>你的回答</small><p>我先说明适用人群和证据边界，再回答您最关心的问题。</p></div><div className="sim-preview-result"><strong>✦ AI 沟通判断</strong><span>回应关注点 · 说明边界</span></div></div>
        </section>
        <section className="game-panel p-5 sm:p-6" aria-label="训练核心能力">
          <div className="flex items-center justify-between border-b border-[#2e4e61] pb-4"><h2 className="text-sm font-bold">核心能力</h2><span className="game-kicker !text-[9px]">OBJECTIVES</span></div>
          <ol className="mt-2 space-y-1">
            {[
              ["01", "准确传递证据", "说清适用人群和资料局限"],
              ["02", "完整表达风险", "不回避不确定性"],
              ["03", "守住沟通边界", "超出资料时停止推断"],
            ].map(([n, title, detail]) => <li key={n} className="flex gap-3 py-2.5"><span className="grid h-7 w-7 shrink-0 place-items-center rounded border border-[#46738a] text-[10px] font-bold text-[#83dff0]">{n}</span><div><strong className="block text-xs text-[#e3f3f8]">{title}</strong><span className="text-[11px] text-[#8daabb]">{detail}</span></div></li>)}
          </ol>
        </section>
      </div>

      <section className="mt-8">
        <div className="mb-3 flex items-end justify-between gap-3"><div><p className="game-kicker">TRAINING PROGRAMS</p><h2 className="mt-1.5 text-lg font-bold">选择训练课程</h2></div><Link className="game-link text-xs" to="/products">查看信达产品目录 →</Link></div>
        <div className="grid gap-3 md:grid-cols-2" aria-label="选择训练课程">
          {programs.data?.map((program, index) => (
            <button type="button" key={program.id} aria-pressed={filters.program === program.id}
              onClick={() => setFilters((current) => ({ ...current, program: program.id }))}
              className={`flex min-h-[90px] items-center gap-4 rounded-lg border p-4 text-left transition-colors ${filters.program === program.id ? "border-[#79d7ed] bg-[#194358] shadow-[inset_3px_0_#79d7ed]" : "border-[#2e5065] bg-[#102638] hover:border-[#5a9cb5] hover:bg-[#153348]"}`}>
              <span className="text-2xl font-bold text-[#7bd7ed]">0{index + 1}</span>
              <span className="min-w-0 flex-1"><strong className="block text-sm text-[#f1f9fc]">{program.title}</strong><small className="mt-1 block text-[11px] leading-5 text-[#9bb6c5]">{program.description}</small></span>
              <span aria-hidden="true" className="text-lg text-[#77d5eb]">↗</span>
            </button>
          ))}
          {programs.error && <div className="game-alert">课程加载失败：{programs.error}</div>}
        </div>
      </section>

      <section className="mt-8">
        <div className="mb-3 flex items-end justify-between gap-3"><div><p className="game-kicker">MISSION ARCHIVE</p><h2 className="mt-1.5 text-lg font-bold">可选情境</h2></div><span className="text-xs text-[#8eacbc]">{data ? `${data.length} 个任务` : ""}</span></div>
        <div className="game-panel flex flex-wrap items-end gap-3 p-4">
          <FilterSelect label="科室" value={filters.dept ?? ""} options={DEPARTMENTS.map((v) => ({ value: v, label: DEPT_LABEL[v] }))} onChange={(v) => setFilters((current) => ({ ...current, dept: (v || undefined) as Department | undefined }))} />
          <FilterSelect label="难度" value={filters.difficulty ?? ""} options={DIFFICULTIES.map((v) => ({ value: v, label: DIFFICULTY_LABEL[v] }))} onChange={(v) => setFilters((current) => ({ ...current, difficulty: (v || undefined) as Difficulty | undefined }))} />
          <FilterSelect label="情境" value={filters.type ?? ""} options={SCENARIO_TYPES.map((v) => ({ value: v, label: TYPE_LABEL[v] }))} onChange={(v) => setFilters((current) => ({ ...current, type: (v || undefined) as ScenarioType | undefined }))} />
        </div>
        {startError && <div className="game-alert mt-3">进入任务失败：{startError}</div>}
        {loading && <div className="game-panel mt-3 p-10 text-center text-sm text-[#9eb8c7]">正在载入任务…</div>}
        {error && <div className="game-alert mt-3">加载失败：{error}</div>}
        {data?.length === 0 && <div className="game-panel mt-3 p-10 text-center text-sm text-[#9eb8c7]">没有符合条件的任务，请调整筛选。</div>}
        <div className="mt-3 grid gap-3 lg:grid-cols-2">
          {data?.map((scenario, index) => (
            <article key={scenario.id} className="game-card flex min-h-[220px] flex-col p-5">
              <div className="flex items-center justify-between gap-3"><span className="game-kicker !text-[10px]">MISSION {String(index + 1).padStart(2, "0")}</span><DifficultyBadge value={scenario.difficulty} /></div>
              <h3 className="mt-3 text-[15px] font-bold leading-6 text-[#edf8fc]">{scenario.rep_goal}</h3>
              <p className="game-muted mt-1.5 line-clamp-2 text-xs leading-6">{scenario.context_brief}</p>
              <div className="mt-3 flex flex-wrap gap-1.5"><Tag>{DEPT_LABEL[scenario.department]}</Tag><Tag>{TYPE_LABEL[scenario.type]}</Tag></div>
              <div className="mt-auto flex items-center gap-4 pt-4">
                <button type="button" className="game-btn" disabled={!SESSION_ENABLED || !!startingId} onClick={() => void start(scenario.id)}>
                  {startingId === scenario.id ? "正在进入…" : "开始任务"}<span aria-hidden="true">→</span>
                </button>
                <Link className="game-link" to={`/scenarios/${scenario.id}${diaryId ? `?diary=${encodeURIComponent(diaryId)}` : ""}`}>查看任务简报</Link>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
