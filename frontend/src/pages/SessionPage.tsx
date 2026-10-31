import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { guidedStep, QUALITY_LABEL } from "../guided";
import { END_REASON_LABEL, SIGNAL_LABEL, SIGNAL_POLARITY } from "../labels";
import { readHints, writeHints } from "../lib/rep";
import { speakDoctorReply, speechOutputAvailable } from "../speech";
import type { ScenarioDetail, SessionView, TurnView } from "../types";
import { startVoiceInput, voiceInputAvailable } from "../voice";

const msg = (e: unknown) => (e instanceof Error ? e.message : String(e));

function Meter({ label, value, color }: { label: string; value: number; color: string }) {
  return <div className="mt-4"><div className="mb-2 flex justify-between text-[11px] text-[#b3cbd7]"><span>{label}</span><strong>{value}</strong></div><div className="game-meter"><div style={{ width: `${value}%`, background: color }} /></div></div>;
}

function Bubble({ turn, onSpeak }: { turn: TurnView; onSpeak?: (text: string) => void }) {
  const rep = turn.speaker === "rep";
  return <div className={`mb-5 flex gap-3 ${rep ? "flex-row-reverse" : ""}`}>
    <div className={`grid h-8 w-8 shrink-0 place-items-center rounded-md border text-xs font-bold ${rep ? "border-[#5b96a8] bg-[#28657a] text-[#e6f8fc]" : "border-[#497287] bg-[#1b4055] text-[#d8edf5]"}`}>{rep ? "我" : "医"}</div>
    <div className="max-w-[82%] sm:max-w-[74%]"><div className={`mb-1.5 flex items-center gap-2 text-[10px] font-bold tracking-wider text-[#95b3c3] ${rep ? "justify-end" : ""}`}><span>{rep ? "你 · 医药代表" : "模拟医生"}</span>{!rep && onSpeak && <button type="button" className="game-link border-0 bg-transparent p-0 text-[10px]" onClick={() => onSpeak(turn.text)} aria-label="朗读这句模拟医生回复">🔊 朗读</button>}</div><div className={`game-bubble ${rep ? "rep" : ""}`}>{turn.text}</div></div>
  </div>;
}

function MicIcon() {
  return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="2" width="6" height="12" rx="3" /><path d="M5 10a7 7 0 0 0 14 0M12 17v5m-4 0h8" /></svg>;
}

export default function SessionPage() {
  const { id = "" } = useParams();
  const nav = useNavigate();
  const [session, setSession] = useState<SessionView | null>(null);
  const [scenario, setScenario] = useState<ScenarioDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [input, setInput] = useState("");
  const [guided, setGuided] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [hints, setHints] = useState(readHints());
  const [voiceListening, setVoiceListening] = useState(false);
  const [speechEnabled, setSpeechEnabled] = useState(false);
  const speechEnabledRef = useRef(false);
  const speechStopRef = useRef<(() => void) | null>(null);
  const voiceStopRef = useRef<(() => void) | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => () => { voiceStopRef.current?.(); speechStopRef.current?.(); }, []);

  function speak(text: string) {
    speechStopRef.current?.();
    speechStopRef.current = speakDoctorReply(text, (reason) => setError(reason));
  }

  function toggleSpeech() {
    const enabled = !speechEnabledRef.current;
    speechEnabledRef.current = enabled;
    setSpeechEnabled(enabled);
    if (enabled) {
      const latest = [...(session?.turns ?? [])].reverse().find((turn) => turn.speaker === "doctor");
      if (latest) speak(latest.text);
    } else { speechStopRef.current?.(); speechStopRef.current = null; }
  }

  function toggleVoice() {
    if (voiceListening) {
      voiceStopRef.current?.();
      return;
    }
    setError(null);
    speechStopRef.current?.();
    speechStopRef.current = null;
    voiceStopRef.current?.();
    voiceStopRef.current = startVoiceInput(
      (text) => setInput((current) => current ? `${current}，${text}` : text),
      setError,
      setVoiceListening,
    );
  }

  useEffect(() => {
    let off = false;
    (async () => {
      try {
        const s = await api.getSession(id);
        if (off) return;
        setSession(s);
        setGuided(false);
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
    if (!text || sending || voiceListening || ended || !session) return;
    voiceStopRef.current?.();
    setVoiceListening(false);
    const before = session;
    setSending(true);
    setError(null);
    setInput("");
    setSession({ ...before, turns: [...before.turns, { idx: before.turns.length, speaker: "rep", text, signals: [], state_after: null, judge_note: "", judge_degraded: false }] });
    try {
      const result = await api.sendTurn(before.id, text);
      setSession(await api.getSession(before.id));
      if (speechEnabledRef.current) speak(result.doctor_reply);
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
    try { const out = await api.createSession(session.scenario_id, session.rehearsal_note ? session.diary_id : null); nav(`/session/${out.session_id}`); }
    catch (e) { setError(msg(e)); }
  }

  if (!session && !error) return <div className="game-panel p-10 text-center text-sm text-[#9bb7c6]">正在进入对话关卡…</div>;
  if (!session) return <div className="game-alert">{error}　<Link className="game-link" to="/home">返回任务大厅</Link></div>;

  return <div>
    {session.rehearsal_note && <div className="game-alert mb-4" role="status"><strong>本轮日记线索：</strong>{session.rehearsal_note}{session.rehearsal_mood && <p className="mt-2 text-xs font-bold">本场模拟节奏：{session.rehearsal_mood === "rushed" ? "医生较忙，回答会更简短" : "医生显得不耐烦，可能打断空泛表达"}</p>}<p className="mt-2 text-xs">这是你的主观回忆，只用于虚构演练的沟通风格。若再次使用日记中被指出的表达，模拟医生可能提出异议；这不代表真实医生的观点。</p></div>}
    <header className="sim-header"><div className="sim-header-copy"><p className="sim-eyebrow">LIVE SIMULATION <span>·</span> AI 拜访演练</p><h1>{scenario?.rep_goal ?? "正在加载任务目标"}</h1><p>你来回答，模拟医生继续追问。每一句都有沟通判断。</p><div className="sim-header-meta"><span>● {ended ? "演练已结束" : "演练进行中"}</span><span>第 {repTurns.length + 1} 轮</span><span>实时互动</span></div></div><div className="sim-orbit" aria-hidden="true"><span className="sim-orbit-center">AI</span><i /><i /><i /></div></header>
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_280px]">
      <section className={`game-panel game-chat ${guided ? "guided" : ""}`}>
        <div className="sim-chat-top"><div><strong>模拟拜访现场</strong><p>{guided ? "三步引导教学 · 选择回答并查看反馈" : "直接回答医生 · 说完或写完后发送"}</p></div>{speechOutputAvailable() && <button className="sim-sound" type="button" aria-pressed={speechEnabled} onClick={toggleSpeech}>{speechEnabled ? "关闭朗读" : "听医生说话"}</button>}</div>
        {scenario && <details className="border-b border-[#2b4d61] bg-[#173347] px-5 py-3"><summary className="cursor-pointer text-xs font-semibold text-[#b9dfea]">查看任务目标与背景</summary><p className="mt-3 text-xs leading-6 text-[#bdd2dc]">{scenario.context_brief}</p><ul className="mt-2 list-inside list-disc text-xs leading-6 text-[#bdd2dc]">{scenario.success_criteria.map((criterion) => <li key={criterion}>{criterion}</li>)}</ul></details>}
        <div className="game-chat-log p-4 sm:p-6" aria-live="polite">{turns.map((turn) => <Bubble key={turn.idx} turn={turn} onSpeak={speechOutputAvailable() ? speak : undefined} />)}{sending && <div className="text-xs text-[#9fbccb]">模拟医生正在回应…</div>}<div ref={bottomRef} /></div>
        {error && <div className="game-alert mx-4 mb-2">{error}</div>}
        {lastRep && !sending && <section className="sim-judgement" aria-live="polite"><div className="sim-judge-heading"><span className="sim-ai-badge">✦</span><div><strong>AI 沟通判断</strong><small>{lastRep.judge_degraded ? "备用规则提示" : "本轮回答"}</small></div><span className="sim-judge-round">第 {repTurns.length} 轮</span></div><p>{lastRep.judge_note || (lastRep.judge_degraded ? "模型暂不可用，请稍后再试；本轮仅显示备用沟通提示。" : "暂未识别到明确的沟通动作，可以更具体地回应医生。")}</p><div className="sim-signal-list">{lastRep.signals.map((signal) => <span key={signal} className={SIGNAL_POLARITY[signal] === "good" ? "positive" : "caution"}>{SIGNAL_LABEL[signal]}</span>)}</div><small className="sim-judge-disclaimer">仅作模拟训练参考，医学与合规内容请以正式资料为准。</small></section>}
        {guided && showFeedback && selected && <div className={`game-guided-feedback ${selected.quality}`} role="status"><strong>{QUALITY_LABEL[selected.quality]}</strong><p>{selected.feedback}</p>{recommended && <p className="mt-2"><b>可以这样说：</b>{recommended.text}</p>}{!ended && step && <button className="game-btn mt-3" type="button" onClick={() => setShowFeedback(false)}>进入第 {repTurns.length + 1} 题 →</button>}</div>}
        {ended ? <div className="border-t border-[#2b4d61] bg-[#102638] p-4"><div className="mb-3 text-xs font-semibold text-[#d9eaf1]">演练结束：{session.end_reason ? END_REASON_LABEL[session.end_reason] : "已结束"}</div><div className="flex flex-wrap gap-2"><Link className="game-btn" to={`/review/${session.id}`}>查看复盘 →</Link><button className="game-btn game-btn-outline" type="button" onClick={() => void again()}>再练一次</button><Link className="game-btn game-btn-outline" to="/home">返回任务大厅</Link></div></div> : guided ? <div className="game-guided-panel">
          {scenario ? <><div className="flex flex-wrap items-center justify-between gap-2"><span className="game-kicker">GUIDED TRAINING / 引导教学</span><span className="text-xs font-bold text-[#bdd6e2]">{Math.min(repTurns.length + 1, 3)} / 3</span></div>
            {showFeedback && selected ? (!step && <div className="mt-4"><p className="mb-3 text-sm text-[#d8eaf2]">三步教学已完成。现在可以查看逐句复盘，或切换到自由练习。</p><button className="game-btn" type="button" onClick={() => void finish(true)}>结束并查看复盘 →</button></div>) : step ? <><h2 className="mt-3 text-base font-bold text-[#eef9fc]">第 {repTurns.length + 1} 题 · {step.title}</h2><p className="mt-1 text-xs text-[#bdd2dc]">{step.prompt}</p><div className="mt-3 grid gap-2">{step.choices.map((option, index) => <button key={option.text} className="game-choice" type="button" disabled={sending} onClick={() => void send(option.text)}><span className="game-choice-letter">{String.fromCharCode(65 + index)}</span><span>{option.text}</span></button>)}</div></> : <p className="mt-3 text-xs text-[#bdd2dc]">这次对话已超过引导教学的三步，可继续自由练习。</p>}
          </> : <p className="text-xs text-[#bdd2dc]">正在加载题目…</p>}
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-[#2b4d61] pt-3"><button className="game-link border-0 bg-transparent p-0" type="button" onClick={() => { setGuided(false); setShowFeedback(false); }}>切换到自由练习</button><button className="border-0 bg-transparent text-xs text-[#a6c2d0] hover:text-white" type="button" onClick={() => void finish()}>提前结束演练</button></div>
          <p className="mt-2 text-[10px] leading-5 text-[#88a7b8]">选项与反馈仅用于模拟教学，医学及合规内容请以正式资料和带教审核为准。</p>
        </div> : <div className="sim-composer"><div className="sim-composer-title"><div><strong>轮到你了</strong><span>说出你的回答，AI 会继续扮演医生并给出判断</span></div><button type="button" onClick={() => setGuided(true)}>试试三步引导 ↗</button></div><label className="sr-only" htmlFor="rep-message">输入你的回应</label><textarea id="rep-message" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void send(); } }} rows={3} maxLength={2000} disabled={sending} placeholder="你会怎么回答医生？可以打字，也可以点麦克风说出来…" className="sim-input" /><div className="sim-composer-actions"><button className="sim-end" type="button" onClick={() => void finish()}>结束演练</button><div><span className="sim-input-hint">开始后持续收音，点停止结束</span>{voiceInputAvailable() ? <button className={`sim-mic ${voiceListening ? "listening" : ""}`} type="button" onClick={toggleVoice} disabled={sending} aria-label={voiceListening ? "停止语音输入" : "开始语音输入"}><MicIcon /><span>{voiceListening ? "停止录音" : "语音回答"}</span></button> : <span className="sim-voice-unavailable">当前设备不支持语音</span>}<button className="sim-send" type="button" onClick={() => void send()} disabled={sending || voiceListening || !input.trim()}>{sending ? "AI 思考中…" : "发送回答"}<span aria-hidden="true">↗</span></button></div></div></div>}
      </section>

      <aside className="game-panel h-fit p-5"><div className="flex items-center justify-between gap-3"><h2 className="text-sm font-bold">训练状态</h2><span className="game-kicker !text-[9px]">STATUS</span></div><p className="game-muted mt-2 text-xs leading-6">以下数值仅为模拟训练状态，供练习时参考。</p><label className="mt-5 flex cursor-pointer items-center justify-between border-y border-[#2d4e61] py-3 text-xs text-[#c6dbe5]"><span>显示实时提示</span><input className="h-4 w-4 accent-[#79d9ed]" type="checkbox" checked={hints} onChange={(e) => { setHints(e.target.checked); writeHints(e.target.checked); }} /></label>{hints ? <>{state && <div className="pb-2"><Meter label="模拟信任" value={state.trust} color="#78d8bc" /><Meter label="模拟耐心" value={state.patience} color="#e8c27f" /><Meter label="模拟兴趣" value={state.engagement} color="#78d7ed" /></div>}<div className="mt-4 border-t border-[#2d4e61] pt-4 text-[11px] font-bold text-[#c6dbe5]">上一句识别结果</div><div className="mt-2 flex flex-wrap gap-1.5">{(lastRep?.signals.length ?? 0) === 0 && <span className="text-xs text-[#8ba9ba]">暂无明确提示</span>}{lastRep?.signals.map((signal) => <span key={signal} className={`game-tag ${SIGNAL_POLARITY[signal] === "good" ? "game-easy" : "game-hard"}`}>{SIGNAL_LABEL[signal]}</span>)}</div></> : <p className="mt-4 text-xs text-[#8ba9ba]">实时提示已隐藏。</p>}<p className="mt-6 text-[11px] leading-5 text-[#819eaf]">模型可能遗漏沟通行为；不能据此判断真实医生态度或合规结果。</p></aside>
    </div>
  </div>;
}
