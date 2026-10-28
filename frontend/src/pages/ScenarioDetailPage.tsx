import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { DifficultyBadge, Tag } from "../components/Badge";
import { useAsync } from "../hooks";
import { DEPT_LABEL, TYPE_LABEL } from "../labels";
import { getRepId } from "../lib/rep";

const SESSION_ENABLED = import.meta.env.VITE_ENABLE_SESSION === "1";

export default function ScenarioDetailPage() {
  const { id = "" } = useParams();
  const nav = useNavigate();
  const { data, error, loading } = useAsync(() => api.getScenario(id), [id]);
  const [starting, setStarting] = useState(false);
  const [startErr, setStartErr] = useState<string | null>(null);
  const [preGoal, setPreGoal] = useState("");

  async function start() {
    if (!data) return;
    setStarting(true);
    setStartErr(null);
    try {
      const out = await api.createSession(data.id, getRepId(), preGoal.trim());
      nav(`/session/${out.session_id}`);
    } catch (e) {
      setStartErr(e instanceof Error ? e.message : String(e));
      setStarting(false);
    }
  }

  if (loading) return <div className="py-12 text-center text-slate-500">加载中…</div>;
  if (error || !data) {
    return (
      <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
        {error ?? "场景不存在"}　<Link className="underline" to="/">返回列表</Link>
      </div>
    );
  }
  const p = data.persona_public;
  const settingText = ["where", "duration", "state"]
    .map((k) => data.setting?.[k])
    .filter((v): v is string => !!v)
    .join("｜");
  const goalOk = preGoal.trim().length >= 6;

  return (
    <div className="mx-auto max-w-3xl">
      <Link to="/" className="text-sm text-slate-500 hover:underline">← 返回场景列表</Link>
      <div className="mt-3 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <Tag>{DEPT_LABEL[data.department]}</Tag>
          <Tag>{TYPE_LABEL[data.type]}</Tag>
          <DifficultyBadge value={data.difficulty} />
          {data.hard_gate && <Tag>合规红线场景</Tag>}
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

        {data.pre_info && (
          <section className="mb-4">
            <h2 className="mb-1 text-sm font-medium text-slate-500">上次拜访记录</h2>
            <p className="text-sm leading-relaxed">{data.pre_info}</p>
          </section>
        )}

        {settingText && (
          <section className="mb-4">
            <h2 className="mb-1 text-sm font-medium text-slate-500">现场情况</h2>
            <p className="text-sm">{settingText}</p>
          </section>
        )}

        <section className="mb-6">
          <h2 className="mb-1 text-sm font-medium text-slate-500">本次训练的达成标准</h2>
          <ul className="list-inside list-disc text-sm leading-relaxed">
            {data.success_criteria.map((c) => (<li key={c}>{c}</li>))}
          </ul>
        </section>

        <section className="mb-4">
          <h2 className="mb-1 text-sm font-medium text-slate-500">拜访前：写一句你这次的目标</h2>
          <textarea
            value={preGoal}
            onChange={(e) => setPreGoal(e.target.value)}
            rows={2}
            maxLength={200}
            placeholder="让主任同意下周再聊十分钟，只谈已获批的适应症"
            className="w-full resize-none rounded-md border border-slate-300 p-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
          {!goalOk && <p className="mt-1 text-xs text-slate-400">至少写 6 个字才能开始</p>}
        </section>

        {startErr && <div className="mb-3 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{startErr}</div>}
        <button
          type="button"
          onClick={() => void start()}
          disabled={!SESSION_ENABLED || starting || !goalOk}
          title={SESSION_ENABLED ? (goalOk ? "" : "请先写下这次的目标") : "演练功能即将开放"}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {!SESSION_ENABLED ? "开始演练（即将开放）" : starting ? "正在进入…" : "开始演练"}
        </button>
      </div>
    </div>
  );
}
