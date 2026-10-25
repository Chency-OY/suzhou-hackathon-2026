import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { DifficultyBadge, Tag } from "../components/Badge";
import { useAsync } from "../hooks";
import { DEPT_LABEL, DIFFICULTY_LABEL, TYPE_LABEL } from "../labels";
import {
  DEPARTMENTS, DIFFICULTIES, SCENARIO_TYPES,
  type Department, type Difficulty, type ScenarioFilters, type ScenarioType,
} from "../types";

function FilterSelect({ label, value, options, onChange }: {
  label: string; value: string; options: { value: string; label: string }[]; onChange: (v: string) => void;
}) {
  return (
    <label className="flex items-center gap-2 text-sm text-slate-600">
      <span className="shrink-0">{label}</span>
      <select
        className="rounded-md border border-slate-300 bg-white px-2 py-2 text-sm text-slate-800"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">全部</option>
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </label>
  );
}

export default function ScenarioListPage() {
  const [filters, setFilters] = useState<ScenarioFilters>({ program: "general" });
  const programs = useAsync(() => api.listPrograms(), []);
  const { data, error, loading } = useAsync(
    () => api.listScenarios(filters),
    [filters.program, filters.dept, filters.difficulty, filters.type],
  );

  return (
    <div>
      <div className="mb-8 border-b border-slate-200 pb-7">
        <p className="mb-2 text-xs font-semibold tracking-[0.18em] text-teal-700">REP TRAINER · TRAINING STUDIO</p>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">从一次真实的对话开始练习</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600">
          选择情境，与虚构医生交流，结束后回看自己的表达。先练会提问、倾听和守住证据边界，再练具体产品资料。
        </p>
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          <div className="rounded-lg border border-sky-100 bg-sky-50 p-4"><strong className="text-sm text-sky-900">证据准确</strong><p className="mt-1 text-xs leading-5 text-slate-600">说清资料来源、适用人群和研究局限。</p></div>
          <div className="rounded-lg border border-sky-100 bg-sky-50 p-4"><strong className="text-sm text-sky-900">风险完整</strong><p className="mt-1 text-xs leading-5 text-slate-600">不回避安全性问题和不确定性。</p></div>
          <div className="rounded-lg border border-sky-100 bg-sky-50 p-4"><strong className="text-sm text-sky-900">守住边界</strong><p className="mt-1 text-xs leading-5 text-slate-600">遇到超出批准资料的问题，及时停止推断并转交核实。</p></div>
        </div>
      </div>

      <div className="mb-7 grid gap-3 sm:grid-cols-2" aria-label="选择训练课程">
        {programs.data?.map((program) => {
          const selected = filters.program === program.id;
          return (
            <button
              type="button"
              key={program.id}
              aria-pressed={selected}
              onClick={() => setFilters((f) => ({ ...f, program: program.id }))}
              className={`rounded-xl border p-4 text-left transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-700 ${
                selected ? "border-teal-700 bg-teal-50 shadow-sm" : "border-slate-200 bg-white hover:border-slate-400"
              }`}
            >
              <div className="mb-2 flex items-center justify-between">
                <h2 className="font-semibold text-slate-900">{program.title}</h2>
                <span className={`text-xs font-medium ${selected ? "text-teal-800" : "text-slate-400"}`}>
                  {selected ? "正在查看" : "选择课程"}
                </span>
              </div>
              <p className="text-sm leading-6 text-slate-600">{program.description}</p>
            </button>
          );
        })}
        {programs.error && <p className="text-sm text-rose-700">课程加载失败：{programs.error}</p>}
      </div>

      <div className="mb-5 flex flex-wrap items-center gap-x-5 gap-y-3 border-b border-slate-200 pb-5">
        <FilterSelect label="科室" value={filters.dept ?? ""}
          options={DEPARTMENTS.map((d) => ({ value: d, label: DEPT_LABEL[d] }))}
          onChange={(v) => setFilters((f) => ({ ...f, dept: (v || undefined) as Department | undefined }))} />
        <FilterSelect label="难度" value={filters.difficulty ?? ""}
          options={DIFFICULTIES.map((d) => ({ value: d, label: DIFFICULTY_LABEL[d] }))}
          onChange={(v) => setFilters((f) => ({ ...f, difficulty: (v || undefined) as Difficulty | undefined }))} />
        <FilterSelect label="情境" value={filters.type ?? ""}
          options={SCENARIO_TYPES.map((t) => ({ value: t, label: TYPE_LABEL[t] }))}
          onChange={(v) => setFilters((f) => ({ ...f, type: (v || undefined) as ScenarioType | undefined }))} />
        <span className="text-sm text-slate-500 sm:ml-auto">{data ? `${data.length} 个可练情境` : ""}</span>
      </div>

      {loading && <div className="py-12 text-center text-sm text-slate-500">正在加载情境…</div>}
      {error && <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">加载失败：{error}</div>}
      {data?.length === 0 && <div className="py-12 text-center text-sm text-slate-500">没有符合条件的情境，请调整筛选。</div>}

      <div className="grid gap-4 md:grid-cols-2">
        {data?.map((s) => (
          <Link key={s.id} to={`/scenarios/${s.id}`}
            className="group flex flex-col rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-teal-600 hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-700">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <Tag>{TYPE_LABEL[s.type]}</Tag><Tag>{DEPT_LABEL[s.department]}</Tag><DifficultyBadge value={s.difficulty} />
            </div>
            <h3 className="text-base font-semibold leading-6 text-slate-900">{s.rep_goal}</h3>
            <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-600">{s.context_brief}</p>
            <span className="mt-4 text-sm font-medium text-teal-700 group-hover:underline">查看情境并开始练习 →</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
