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
      {label}
      <select
        className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">全部</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </label>
  );
}

export default function ScenarioListPage() {
  const [filters, setFilters] = useState<ScenarioFilters>({});
  const { data, error, loading } = useAsync(
    () => api.listScenarios(filters),
    [filters.dept, filters.difficulty, filters.type],
  );

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-4">
        <FilterSelect
          label="科室" value={filters.dept ?? ""}
          options={DEPARTMENTS.map((d) => ({ value: d, label: DEPT_LABEL[d] }))}
          onChange={(v) => setFilters((f) => ({ ...f, dept: (v || undefined) as Department | undefined }))}
        />
        <FilterSelect
          label="难度" value={filters.difficulty ?? ""}
          options={DIFFICULTIES.map((d) => ({ value: d, label: DIFFICULTY_LABEL[d] }))}
          onChange={(v) => setFilters((f) => ({ ...f, difficulty: (v || undefined) as Difficulty | undefined }))}
        />
        <FilterSelect
          label="类型" value={filters.type ?? ""}
          options={SCENARIO_TYPES.map((t) => ({ value: t, label: TYPE_LABEL[t] }))}
          onChange={(v) => setFilters((f) => ({ ...f, type: (v || undefined) as ScenarioType | undefined }))}
        />
        <div className="ml-auto text-sm text-slate-500">{data ? `共 ${data.length} 个场景` : ""}</div>
      </div>

      {loading && <div className="py-12 text-center text-slate-500">加载中…</div>}
      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">加载失败：{error}</div>
      )}
      {data && data.length === 0 && (
        <div className="py-12 text-center text-slate-500">没有符合条件的场景，试试调整筛选条件。</div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {data?.map((s) => (
          <Link
            key={s.id}
            to={`/scenarios/${s.id}`}
            className="flex flex-col rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-slate-400 hover:shadow"
          >
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <Tag>{DEPT_LABEL[s.department]}</Tag>
              <Tag>{TYPE_LABEL[s.type]}</Tag>
              <DifficultyBadge value={s.difficulty} />
            </div>
            <div className="mb-1 text-sm font-medium">{s.rep_goal}</div>
            <p className="line-clamp-3 text-sm text-slate-500">{s.context_brief}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
