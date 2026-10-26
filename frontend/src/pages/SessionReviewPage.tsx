import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { useAsync } from "../hooks";
import { END_REASON_LABEL, SIGNAL_LABEL, SIGNAL_POLARITY, TYPE_LABEL } from "../labels";
import type { Signal, TurnView } from "../types";

const positive: Signal[] = ["asked_open_question", "empathy_shown", "proposed_next_step", "relevant_to_concern", "addressed_objection", "cited_evidence"];
const negative: Signal[] = ["exaggeration", "pushy", "off_label_claim", "competitor_bashing", "ignored_doctor_question", "vague_or_generic"];
const count = (turns: TurnView[], signal: Signal) => turns.filter((turn) => turn.speaker === "rep" && turn.signals.includes(signal)).length;

export default function SessionReviewPage() {
  const { id = "" } = useParams();
  const { data, error, loading } = useAsync(async () => {
    const session = await api.getSession(id);
    const scenario = await api.getScenario(session.scenario_id);
    return { session, scenario };
  }, [id]);

  if (loading) return <div className="game-panel p-10 text-center text-sm text-[#9bb7c6]">正在整理对话记录…</div>;
  if (error || !data) return <div className="game-alert">{error || "未找到会话"}</div>;

  const { session, scenario } = data;
  const repTurns = session.turns.filter((turn) => turn.speaker === "rep");
  const foundPositive = positive.filter((signal) => count(repTurns, signal) > 0);
  const foundNegative = negative.filter((signal) => count(repTurns, signal) > 0);
  const suggestions = [
    count(repTurns, "asked_open_question") === 0 ? "开场后先问一个开放式问题，例如“您最关注哪类患者管理难点？”" : null,
    foundNegative.length > 0 ? "回看标红的原句：把绝对化或催促式表达改成可核对的证据与征询。" : null,
    count(repTurns, "proposed_next_step") === 0 ? "结束前征求医生意愿，提出一个具体且不影响诊疗的后续交流方式。" : null,
  ].filter((item): item is string => item !== null);

  return <div className="mx-auto max-w-5xl">
    <Link to="/progress" className="game-link">← 返回练习档案</Link>
    <section className="game-hero mt-5 p-6 sm:p-8"><p className="game-kicker">DEBRIEF / 任务复盘</p><h1 className="game-title mt-3 !text-[clamp(22px,2.7vw,32px)]">{TYPE_LABEL[scenario.type]} · {scenario.rep_goal}</h1><div className="mt-5 flex flex-wrap gap-x-5 gap-y-2 text-xs text-[#b7d2de]"><span>{new Date(session.started_at).toLocaleString("zh-CN")}</span><span>{repTurns.length} 次代表发言</span><span>{session.end_reason ? END_REASON_LABEL[session.end_reason] : "演练尚未结束"}</span></div></section>
    <div className="mt-4 rounded-lg border border-[#755c36] bg-[#3c3020] p-4 text-xs leading-6 text-[#edd4a4]">此处只显示规则识别到的沟通行为与原句，没有自动评分。未识别到某项行为不等于没有做到；医学与合规内容需核对正式资料并由带教人员复核。</div>

    <div className="mt-4 grid gap-4 md:grid-cols-2">
      <section className="game-panel p-5"><div className="flex items-center justify-between"><h2 className="text-sm font-bold">有效表达</h2><span className="game-kicker !text-[9px]">POSITIVE</span></div>{foundPositive.length ? <ul className="mt-4 space-y-2">{foundPositive.map((signal) => <li key={signal} className="flex justify-between gap-4 border-b border-[#2a4c60] pb-2 text-xs text-[#c7dbe4]"><span>{SIGNAL_LABEL[signal]}</span><strong className="text-[#91e0c9]">{count(repTurns, signal)} 次</strong></li>)}</ul> : <p className="game-muted mt-4 text-xs leading-6">暂无明确识别结果，可以结合原句自行回看。</p>}</section>
      <section className="game-panel p-5"><div className="flex items-center justify-between"><h2 className="text-sm font-bold">需要留意</h2><span className="game-kicker !text-[9px]">REVIEW</span></div>{foundNegative.length ? <ul className="mt-4 space-y-2">{foundNegative.map((signal) => <li key={signal} className="flex justify-between gap-4 border-b border-[#2a4c60] pb-2 text-xs text-[#c7dbe4]"><span>{SIGNAL_LABEL[signal]}</span><strong className="text-[#efb4bc]">{count(repTurns, signal)} 次</strong></li>)}</ul> : <p className="game-muted mt-4 text-xs leading-6">规则没有识别到明确的风险表达，这不代表已经完成合规审核。</p>}</section>
    </div>

    {suggestions.length > 0 && <section className="game-panel mt-4 p-5"><div className="flex items-center justify-between"><h2 className="text-sm font-bold">下一次可以尝试</h2><span className="game-kicker !text-[9px]">NEXT MISSION</span></div><ul className="mt-4 space-y-2">{suggestions.map((tip, index) => <li key={tip} className="flex gap-3 text-xs leading-6 text-[#c6d9e3]"><span className="text-[#80d8eb]">0{index + 1}</span><span>{tip}</span></li>)}</ul></section>}

    <section className="game-panel mt-4 p-5 sm:p-7"><div className="flex items-center justify-between"><h2 className="text-sm font-bold">逐句回看</h2><span className="game-kicker !text-[9px]">TRANSCRIPT</span></div><div className="mt-5 space-y-1">{session.turns.map((turn) => <div key={turn.idx} className={`game-transcript ${turn.speaker === "rep" ? "rep" : ""}`}><div className="text-[10px] font-bold tracking-wide text-[#9bb7c5]">{turn.speaker === "rep" ? "你 · 医药代表" : "模拟医生"} / 第 {turn.idx + 1} 句</div><p className="mt-1 whitespace-pre-wrap text-sm leading-7 text-[#d5e4eb]">{turn.text}</p>{turn.signals.length > 0 && <div className="mt-2 flex flex-wrap gap-1.5">{turn.signals.map((signal) => <span key={signal} className={`game-tag ${SIGNAL_POLARITY[signal] === "good" ? "game-easy" : "game-hard"}`}>{SIGNAL_LABEL[signal]}</span>)}</div>}</div>)}</div></section>
    <div className="mt-5 flex flex-wrap gap-2">{!session.ended_at && <Link to={`/session/${session.id}`} className="game-btn">继续演练</Link>}<Link to={`/scenarios/${session.scenario_id}`} className="game-btn game-btn-outline">查看任务简报</Link><Link to="/home" className="game-btn game-btn-outline">选择其他任务</Link></div>
  </div>;
}
