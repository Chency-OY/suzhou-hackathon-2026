import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { DifficultyBadge, Tag } from "../components/Badge";
import { useAsync } from "../hooks";
import { DEPT_LABEL, TYPE_LABEL } from "../labels";

const SESSION_ENABLED = import.meta.env.VITE_ENABLE_SESSION === "1";

export default function ScenarioDetailPage() {
  const { id = "" } = useParams();
  const { data, error, loading } = useAsync(() => api.getScenario(id), [id]);

  if (loading) return <div className="py-12 text-center text-slate-500">加载中…</div>;
  if (error || !data) {
    return (
      <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
        {error ?? "场景不存在"}　<Link className="underline" to="/">返回列表</Link>
      </div>
    );
  }
  const p = data.persona_public;

  return (
    <div className="mx-auto max-w-3xl">
      <Link to="/" className="text-sm text-slate-500 hover:underline">← 返回场景列表</Link>
      <div className="mt-3 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <Tag>{DEPT_LABEL[data.department]}</Tag>
          <Tag>{TYPE_LABEL[data.type]}</Tag>
          <DifficultyBadge value={data.difficulty} />
        </div>
        <h1 className="mb-4 text-lg font-semibold">{data.rep_goal}</h1>

        <section className="mb-4">
          <h2 className="mb-1 text-sm font-medium text-slate-500">拜访背景</h2>
          <p className="text-sm leading-relaxed">{data.context_brief}</p>
        </section>

        <section className="mb-4">
          <h2 className="mb-1 text-sm font-medium text-slate-500">你将面对的医生</h2>
          <p className="text-sm">{p.title}｜{p.hospital_tier}｜{p.style_hint}</p>
        </section>

        <section className="mb-6">
          <h2 className="mb-1 text-sm font-medium text-slate-500">本次训练的达成标准</h2>
          <ul className="list-inside list-disc text-sm leading-relaxed">
            {data.success_criteria.map((c) => (<li key={c}>{c}</li>))}
          </ul>
        </section>

        <button
          type="button"
          disabled={!SESSION_ENABLED}
          title={SESSION_ENABLED ? "" : "演练功能即将开放"}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {SESSION_ENABLED ? "开始演练" : "开始演练（即将开放）"}
        </button>
      </div>
    </div>
  );
}
