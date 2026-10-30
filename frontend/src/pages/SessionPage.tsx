import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { guidedStep, QUALITY_LABEL } from "../guided";
import { END_REASON_LABEL, SIGNAL_LABEL, SIGNAL_POLARITY } from "../labels";
import { readHints, writeHints } from "../lib/rep";
import type { ScenarioDetail, SessionView, TurnView } from "../types";

const msg = (e: unknown) => (e instanceof Error ? e.message : String(e));

function Meter({ label, value, color }: { label: string; value: number; color: string }) {
  return <div className="mt-4"><div className="mb-2 flex justify-between text-[11px] text-[#b3cbd7]"><span>{label}</span><strong>{value}</strong></div><div className="game-meter"><div style={{ width: `${value}%`, background: color }} /></div></div>;
}

function Bubble({ turn }: { turn: TurnView }) {
  const rep = turn.speaker === "rep";
  return <div className={`mb-5 flex gap-3 ${rep ? "flex-row-reverse" : ""}`}>
    <div className={`grid h-8 w-8 shrink-0 place-items-center rounded-md border text-xs font-bold ${rep ? "border-[#5b96a8] bg-[#28657a] text-[#e6f8fc]" : "border-[#497287] bg-[#1b4055] text-[#d8edf5]"}`}>{rep ? "我" : "医"}</div>
    <div className="max-w-[82%] sm:max-w-[74%]"><div className={`mb-1.5 text-[10px] font-bold tracking-wider text-[#95b3c3] ${rep ? "text-right" : ""}`}>{rep ? "你 · 医药代表" : "模拟医生"}</div><div className={`game-bubble ${rep ? "rep" : ""}`}>{turn.text}</div></div>
  </div>;
}

export default function SessionPage() {
  const { id = "" } = useParams();
  const nav = useNavigate();
  const [session, setSession] = useState<SessionView | null>(null);
  const [scenario, setScenario] = useState<ScenarioDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [input, setInput] = useState("");
  const [guided, setGuided] = useState(true);
  const [showFeedback, setShowFeedback] = useState(false);
  const [hints, setHints] = useState(readHints());
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let off = false;
    (async () => {
      try {
        const s = await api.getSession(id);
        if (off) return;
        setSession(s);
        const sc = await api.getScenario(s.scenario_id);
        if (!off) {
          setScenario(sc);
          const rep = s.turns.filter((turn) => turn.speaker === "rep");
          setShowFeedback(!!guidedStep(sc, rep.length - 1)?.choices.some((option) => option.text === rep[rep.length - 1]?.text));
        }
      } catch (e) {
        if (!off) setError(msg(e));
      }
    })();
    return () => { off = true; };
  }, [id]);

  const turns = session?.turns ?? [];
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [turns.length, sending]);
  const ended = !!session?.ended_at;
  const state = [...turns].reverse().find((turn) => turn.state_after)?.state_after ?? null;
  const lastRep = [...turns].reverse().find((turn) => turn.speaker === "rep");
  const repTurns = turns.filter((turn) => turn.speaker === "rep");
  const step = scenario ? guidedStep(scenario, repTurns.length) : null;
  const previousStep = scenario ? guidedStep(scenario, repTurns.length - 1) : null;
  const selected = previousStep?.choices.find((option) => option.text === lastRep?.text);
  const recommended = selected?.quality !== "strong" ? previousStep?.choices.find((option) => option.quality === "strong") : null;

  async function send(chosenText?: string) {
    const text = (chosenText ?? input).trim();
    if (!text || sending || ended || !session) return;
    const before = session;
    setSending(true);
    setError(null);
    setInput("");
    setSession({ ...before, turns: [...before.turns, { idx: before.turns.length, speaker: "rep", text, signals: [], state_after: null }] });
    try {
      const result = await api.sendTurn(before.id, text);
      setSession(await api.getSession(before.id));
      if (result.degraded) setError("本轮使用了备用模拟回应，请核对正式资料后再练习。");
      setShowFeedback(!!chosenText);
    } catch (e) {
      setError(msg(e));
      setInput(text);
      setSession(before);
    } finally { setSending(false); }
  }

  async function finish(openReview = false) {
    if (!session || ended) return;
    try { await api.finishSession(session.id); setSession(await api.getSession(session.id)); if (openReview) nav(`/review/${session.id}`); }
    catch (e) { setError(msg(e)); }
  }

  async function again() {
    if (!session) return;
    try { const out = await api.createSession(session.scenario_id); nav(`/session/${out.session_id}`); }
    catch (e) { setError(msg(e)); }
  }

  if (!session && !error) return <div className="game-panel p-10 text-center text-sm text-[#9bb7c6]">正在进入对话关卡…</div>;
  if (!session) return <div className="game-alert">{error}　<Link className="game-link" to="/home">返回任务大厅</Link></div>;

  return <div>
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3"><div><p className="game-kicker">DIALOGUE SIMULATION / 对话关卡</p><h1 className="mt-1.5 text-xl font-bold text-[#f0f8fc]">{scenario?.rep_goal ?? "正在加载任务目标"}</h1></div><span className="game-tag">{ended ? "本次演练已结束" : "对话进行中"}</span></div>
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_280px]">
      <section className={`game-panel game-chat ${guided ? "guided" : ""}`}>
        <div className="border-b border-[#2b4d61] px-5 py-3"><strong className="text-sm">模拟拜访现场</strong><div className="mt-1 text-[11px] text-[#8daabb]">{guided ? "选择你认为合适的回应，先看反馈，再进入下一步。" : "用自然语言回应医生；你的每句话都会进入复盘。"}</div></div>
        {scenario && <details className="border-b border-[#2b4d61] bg-[#173347] px-5 py-3"><summary className="cursor-pointer text-xs font-semibold text-[#b9dfea]">查看任务目标与背景</summary><p className="mt-3 text-xs leading-6 text-[#bdd2dc]">{scenario.context_brief}</p><ul className="mt-2 list-inside list-disc text-xs leading-6 text-[#bdd2dc]">{scenario.success_criteria.map((criterion) => <li key={criterion}>{criterion}</li>)}</ul></details>}
        <div className="game-chat-log p-4 sm:p-6" aria-live="polite">{turns.map((turn) => <Bubble key={turn.idx} turn={turn} />)}{sending && <div className="text-xs text-[#9fbccb]">模拟医生正在回应…</div>}<div ref={bottomRef} /></div>
        {error && <div className="game-alert mx-4 mb-2">{error}</div>}
        {guided && showFeedback && selected && <div className={`game-guided-feedback ${selected.quality}`} role="status"><strong>{QUALITY_LABEL[selected.quality]}</strong><p>{selected.feedback}</p>{recommended && <p className="mt-2"><b>可以这样说：</b>{recommended.text}</p>}{!ended && step && <button className="game-btn mt-3" type="button" onClick={() => setShowFeedback(false)}>进入第 {repTurns.length + 1} 题 →</button>}</div>}
        {ended ? <div className="border-t border-[#2b4d61] bg-[#102638] p-4"><div className="mb-3 text-xs font-semibold text-[#d9eaf1]">演练结束：{session.end_reason ? END_REASON_LABEL[session.end_reason] : "已结束"}</div><div className="flex flex-wrap gap-2"><Link className="game-btn" to={`/review/${session.id}`}>查看复盘 →</Link><button className="game-btn game-btn-outline" type="button" onClick={() => void again()}>再练一次</button><Link className="game-btn game-btn-outline" to="/home">返回任务大厅</Link></div></div> : guided ? <div className="game-guided-panel">
          {scenario ? <><div className="flex flex-wrap items-center justify-between gap-2"><span className="game-kicker">GUIDED TRAINING / 引导教学</span><span className="text-xs font-bold text-[#bdd6e2]">{Math.min(repTurns.length + 1, 3)} / 3</span></div>
            {showFeedback && selected ? (!step && <div className="mt-4"><p className="mb-3 text-sm text-[#d8eaf2]">三步教学已完成。现在可以查看逐句复盘，或切换到自由练习。</p><button className="game-btn" type="button" onClick={() => void finish(true)}>结束并查看复盘 →</button></div>) : step ? <><h2 className="mt-3 text-base font-bold text-[#eef9fc]">第 {repTurns.length + 1} 题 · {step.title}</h2><p className="mt-1 text-xs text-[#bdd2dc]">{step.prompt}</p><div className="mt-3 grid gap-2">{step.choices.map((option, index) => <button key={option.text} className="game-choice" type="button" disabled={sending} onClick={() => void send(option.text)}><span className="game-choice-letter">{String.fromCharCode(65 + index)}</span><span>{option.text}</span></button>)}</div></> : <p className="mt-3 text-xs text-[#bdd2dc]">这次对话已超过引导教学的三步，可继续自由练习。</p>}
          </> : <p className="text-xs text-[#bdd2dc]">正在加载题目…</p>}
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-[#2b4d61] pt-3"><button className="game-link border-0 bg-transparent p-0" type="button" onClick={() => { setGuided(false); setShowFeedback(false); }}>切换到自由练习</button><button className="border-0 bg-transparent text-xs text-[#a6c2d0] hover:text-white" type="button" onClick={() => void finish()}>提前结束演练</button></div>
          <p className="mt-2 text-[10px] leading-5 text-[#88a7b8]">选项与反馈仅用于模拟教学，医学及合规内容请以正式资料和带教审核为准。</p>
        </div> : <div className="border-t border-[#2b4d61] bg-[#102638] p-3 sm:p-4"><div className="mb-3 flex justify-between gap-3"><strong className="text-xs text-[#d5eaf2]">自由练习</strong><button className="game-link border-0 bg-transparent p-0" type="button" onClick={() => setGuided(true)}>返回引导教学</button></div><label className="sr-only" htmlFor="rep-message">输入你的回应</label><textarea id="rep-message" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void send(); } }} rows={3} maxLength={2000} disabled={sending} placeholder="输入你想对医生说的话…" className="game-field min-h-[76px] resize-y text-sm leading-6" /><div className="mt-2 flex items-center justify-between gap-3"><button className="border-0 bg-transparent text-xs text-[#a6c2d0] hover:text-white" type="button" onClick={() => void finish()}>结束演练</button><div className="flex items-center gap-3"><span className="hidden text-[10px] text-[#80a0b2] sm:block">Enter 发送 · Shift+Enter 换行</span><button className="game-btn" type="button" onClick={() => void send()} disabled={sending || !input.trim()}>发送回应 →</button></div></div></div>}
      </section>

      <aside className="game-panel h-fit p-5"><div className="flex items-center justify-between gap-3"><h2 className="text-sm font-bold">训练状态</h2><span className="game-kicker !text-[9px]">STATUS</span></div><p className="game-muted mt-2 text-xs leading-6">以下数值仅为模拟训练状态，供练习时参考。</p><label className="mt-5 flex cursor-pointer items-center justify-between border-y border-[#2d4e61] py-3 text-xs text-[#c6dbe5]"><span>显示实时提示</span><input className="h-4 w-4 accent-[#79d9ed]" type="checkbox" checked={hints} onChange={(e) => { setHints(e.target.checked); writeHints(e.target.checked); }} /></label>{hints ? <>{state && <div className="pb-2"><Meter label="模拟信任" value={state.trust} color="#78d8bc" /><Meter label="模拟耐心" value={state.patience} color="#e8c27f" /><Meter label="模拟兴趣" value={state.engagement} color="#78d7ed" /></div>}<div className="mt-4 border-t border-[#2d4e61] pt-4 text-[11px] font-bold text-[#c6dbe5]">上一句识别结果</div><div className="mt-2 flex flex-wrap gap-1.5">{(lastRep?.signals.length ?? 0) === 0 && <span className="text-xs text-[#8ba9ba]">暂无明确提示</span>}{lastRep?.signals.map((signal) => <span key={signal} className={`game-tag ${SIGNAL_POLARITY[signal] === "good" ? "game-easy" : "game-hard"}`}>{SIGNAL_LABEL[signal]}</span>)}</div></> : <p className="mt-4 text-xs text-[#8ba9ba]">实时提示已隐藏。</p>}<p className="mt-6 text-[11px] leading-5 text-[#819eaf]">模型可能遗漏沟通行为；不能据此判断真实医生态度或合规结果。</p></aside>
    </div>
  </div>;
}
