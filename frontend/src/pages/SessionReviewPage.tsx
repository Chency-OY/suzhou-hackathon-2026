import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { useAsync } from "../hooks";
import { END_REASON_LABEL, SIGNAL_LABEL, SIGNAL_POLARITY, TYPE_LABEL } from "../labels";
import type { Signal, TurnView } from "../types";

const positive: Signal[] = ["asked_open_question", "empathy_shown", "proposed_next_step", "relevant_to_concern", "addressed_objection", "cited_evidence"];
const negative: Signal[] = ["exaggeration", "pushy", "off_label_claim", "competitor_bashing", "ignored_doctor_question", "vague_or_generic"];

function count(turns: TurnView[], signal: Signal): number {
  return turns.filter((turn) => turn.speaker === "rep" && turn.signals.includes(signal)).length;
}

export default function SessionReviewPage() {
  const { id = "" } = useParams();
  const { data, error, loading } = useAsync(async () => {
    const session = await api.getSession(id);
    const scenario = await api.getScenario(session.scenario_id);
    return { session, scenario };
  }, [id]);

  if (loading) return <div className="py-14 text-center text-sm text-slate-500">正在整理对话…</div>;
  if (error || !data) return <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error || "未找到会话"}</div>;

  const { session, scenario } = data;
  const repTurns = session.turns.filter((turn) => turn.speaker === "rep");
  const foundPositive = positive.filter((signal) => count(repTurns, signal) > 0);
  const foundNegative = negative.filter((signal) => count(repTurns, signal) > 0);
  const suggestions = [
    count(repTurns, "asked_open_question") === 0 ? "开场后先问一个开放式问题，例如“您最关注哪类患者管理难点？”" : null,
    foundNegative.length > 0 ? "回看标红的原句：把绝对化或催促式表达改成可核对的证据与征询。" : null,
    count(repTurns, "proposed_next_step") === 0 ? "结束前征求医生意愿，提出一个具体且不影响诊疗的后续交流方式。" : null,
  ].filter((item): item is string => item !== null);

  return (
    <div className="mx-auto max-w-4xl">
      <Link to="/progress" className="text-sm text-slate-500 hover:underline">← 返回练习记录</Link>
      <div className="mt-4 rounded-xl border border-slate-200 bg-white p-5 sm:p-7">
        <div className="text-xs font-semibold tracking-widest text-teal-700">对话复盘</div>
        <h1 className="mt-2 text-xl font-semibold text-slate-900 sm:text-2xl">{TYPE_LABEL[scenario.type]} · {scenario.rep_goal}</h1>
        <p className="mt-3 text-sm text-slate-600">
          {new Date(session.started_at).toLocaleString("zh-CN")} · {repTurns.length} 次代表发言 ·
          {session.end_reason ? ` ${END_REASON_LABEL[session.end_reason]}` : " 演练尚未结束"}
        </p>
        <div className="mt-5 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm leading-6 text-amber-900">
          此处仅展示规则识别到的沟通行为与原句，没有自动评分。未识别到某项行为不等于你没有做到；医学和合规内容需由正式资料及带教人员复核。
        </div>
      </div>

      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <section className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="font-semibold text-slate-900">识别到的有效表达</h2>
          {foundPositive.length ? <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {foundPositive.map((signal) => <li key={signal} className="flex justify-between gap-4"><span>{SIGNAL_LABEL[signal]}</span><strong>{count(repTurns, signal)} 次</strong></li>)}
          </ul> : <p className="mt-3 text-sm leading-6 text-slate-500">暂无明确识别结果，可以结合下方原句自行回看。</p>}
        </section>
        <section className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="font-semibold text-slate-900">需要留意的表达</h2>
          {foundNegative.length ? <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {foundNegative.map((signal) => <li key={signal} className="flex justify-between gap-4"><span>{SIGNAL_LABEL[signal]}</span><strong>{count(repTurns, signal)} 次</strong></li>)}
          </ul> : <p className="mt-3 text-sm leading-6 text-slate-500">本次规则没有识别到明确的风险表达，这不代表已经完成合规审核。</p>}
        </section>
      </div>

      {suggestions.length > 0 && <section className="mt-5 rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="font-semibold text-slate-900">下次练习可以试试</h2>
        <ul className="mt-3 list-inside list-disc space-y-2 text-sm leading-6 text-slate-700">
          {suggestions.map((tip) => <li key={tip}>{tip}</li>)}
        </ul>
      </section>}

      <section className="mt-5 rounded-xl border border-slate-200 bg-white p-5 sm:p-7">
        <h2 className="font-semibold text-slate-900">逐句回看</h2>
        <div className="mt-4 space-y-4">
          {session.turns.map((turn) => (
            <div key={turn.idx} className={`border-l-2 pl-4 ${turn.speaker === "rep" ? "border-teal-600" : "border-slate-300"}`}>
              <div className="text-xs font-medium text-slate-500">{turn.speaker === "rep" ? "你" : "模拟医生"} · 第 {turn.idx + 1} 句</div>
              <p className="mt-1 whitespace-pre-wrap text-sm leading-7 text-slate-800">{turn.text}</p>
              {turn.signals.length > 0 && <div className="mt-2 flex flex-wrap gap-2">
                {turn.signals.map((signal) => <span key={signal} className={`rounded-full px-2 py-0.5 text-xs ${SIGNAL_POLARITY[signal] === "good" ? "bg-teal-50 text-teal-800" : "bg-rose-50 text-rose-800"}`}>{SIGNAL_LABEL[signal]}</span>)}
              </div>}
            </div>
          ))}
        </div>
      </section>
      <div className="mt-5 flex flex-wrap gap-3">
        {!session.ended_at && <Link to={`/session/${session.id}`} className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white">继续演练</Link>}
        <Link to={`/scenarios/${session.scenario_id}`} className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm">再看这个情境</Link>
        <Link to="/home" className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm">选择其他情境</Link>
      </div>
    </div>
  );
}
