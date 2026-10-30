import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { END_REASON_LABEL, SIGNAL_LABEL, SIGNAL_POLARITY } from "../labels";
import { getRepId, readHints, writeHints } from "../lib/rep";
import type { ScenarioDetail, SessionView, TurnView } from "../types";

const msg = (e: unknown) => (e instanceof Error ? e.message : String(e));

function Bar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="mb-3">
      <div className="mb-1 flex justify-between text-xs text-slate-500">
        <span>{label}</span>
        <span>{value}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-200">
        <div className={`h-full rounded-full transition-all duration-500 ${color}`} style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

const EVENT = /^（([^）]+)）/;

function Bubble({ turn }: { turn: TurnView }) {
  const rep = turn.speaker === "rep";
  const m = !rep ? turn.text.match(EVENT) : null;
  const body = m ? turn.text.slice(m[0].length) : turn.text;
  return (
    <div className={`mb-3 flex ${rep ? "justify-end" : "justify-start"}`}>
      <div className="max-w-[80%]">
        {m && <div className="mb-1 text-xs italic text-slate-400">{m[1]}</div>}
        <div
          className={`whitespace-pre-wrap rounded-2xl px-4 py-2 text-sm leading-relaxed ${
            rep ? "border border-sky-200 bg-sky-100 text-slate-800" : "border border-slate-200 bg-white"
          }`}
        >
          {body}
        </div>
      </div>
    </div>
  );
}

function RecordForm({ sessionId, existing }: { sessionId: string; existing: string | null }) {
  const [note, setNote] = useState(existing ?? "");
  const [state, setState] = useState<"idle" | "saving" | "saved" | "error">(existing ? "saved" : "idle");
  const [err, setErr] = useState<string | null>(null);

  async function save() {
    setState("saving");
    setErr(null);
    try {
      await api.saveRecord(sessionId, note);
      setState("saved");
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  }

  return (
    <div className="mb-3">
      <div className="mb-1 text-sm font-medium">写拜访记录（客户原话、需求、异议、下一步）</div>
      <textarea
        value={note}
        onChange={(e) => { setNote(e.target.value); setState("idle"); }}
        rows={4}
        maxLength={1500}
        className="w-full resize-none rounded-md border border-slate-300 p-2 text-sm"
      />
      <div className="mt-2 flex items-center gap-3">
        <button
          type="button"
          onClick={() => void save()}
          disabled={note.trim().length < 10 || state === "saving"}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm text-white disabled:bg-slate-300"
        >
          保存拜访记录
        </button>
        {state === "saved" && <span className="text-sm text-emerald-600">已保存</span>}
        {err && <span className="text-sm text-rose-600">{err}</span>}
      </div>
    </div>
  );
}

export default function SessionPage() {
  const { id = "" } = useParams();
  const nav = useNavigate();
  const [session, setSession] = useState<SessionView | null>(null);
  const [scenario, setScenario] = useState<ScenarioDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [input, setInput] = useState("");
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
        if (!off) setScenario(sc);
      } catch (e) {
        if (!off) setError(msg(e));
      }
    })();
    return () => {
      off = true;
    };
  }, [id]);

  const turns = session?.turns ?? [];
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns.length, sending]);

  const ended = !!session?.ended_at;
  const state = [...turns].reverse().find((t) => t.state_after)?.state_after ?? null;
  const lastRep = [...turns].reverse().find((t) => t.speaker === "rep");

  async function send() {
    const text = input.trim();
    if (!text || sending || ended || !session) return;
    const before = session;
    setSending(true);
    setError(null);
    setInput("");
    setSession({
      ...before,
      turns: [...before.turns, { idx: before.turns.length, speaker: "rep", text, signals: [], state_after: null }],
    });
    try {
      await api.sendTurn(before.id, text);
      setSession(await api.getSession(before.id));
    } catch (e) {
      setError(msg(e));
      setInput(text);
      setSession(before);
    } finally {
      setSending(false);
    }
  }

  async function finish() {
    if (!session || ended) return;
    try {
      await api.finishSession(session.id);
      setSession(await api.getSession(session.id));
    } catch (e) {
      setError(msg(e));
    }
  }

  async function again() {
    if (!session) return;
    try {
      const out = await api.createSession(session.scenario_id, getRepId());
      nav(`/session/${out.session_id}`);
    } catch (e) {
      setError(msg(e));
    }
  }

  if (!session && !error) return <div className="py-12 text-center text-slate-500">加载中…</div>;
  if (!session) {
    return (
      <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
        {error}　<Link className="underline" to="/">返回场景列表</Link>
      </div>
    );
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_280px]">
      <section className="flex h-[calc(100vh-9rem)] flex-col rounded-xl border border-sky-100 bg-sky-50/70">
        {scenario && (
          <details className="border-b border-slate-200 bg-white px-4 py-2 text-sm">
            <summary className="cursor-pointer font-medium">本次拜访目标：{scenario.rep_goal}</summary>
            <p className="mt-2 text-slate-600">{scenario.context_brief}</p>
            <ul className="mt-2 list-inside list-disc text-slate-600">
              {scenario.success_criteria.map((c) => (<li key={c}>{c}</li>))}
            </ul>
            {session.pre_goal && (
              <div className="mt-3">
                <div className="text-xs font-medium text-slate-500">你的目标</div>
                <p className="mt-1 text-slate-700">{session.pre_goal}</p>
              </div>
            )}
          </details>
        )}

        <div className="flex-1 overflow-y-auto p-4">
          {turns.map((t) => (<Bubble key={t.idx} turn={t} />))}
          {sending && <div className="mb-3 text-sm text-slate-400">医生正在回应…</div>}
          <div ref={bottomRef} />
        </div>

        {error && <div className="mx-4 mb-2 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}

        {ended ? (
          <div className="border-t border-slate-200 bg-white p-4">
            <div className="mb-3 text-sm font-medium">
              演练结束：{session.end_reason ? END_REASON_LABEL[session.end_reason] : "已结束"}
            </div>
            {scenario?.post_task && <RecordForm sessionId={session.id} existing={session.visit_note} />}
            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={again} className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white">
                再练一次
              </button>
              <Link to="/" className="rounded-md border border-slate-300 px-4 py-2 text-sm">返回场景列表</Link>
              <button type="button" disabled className="rounded-md border border-slate-200 px-4 py-2 text-sm text-slate-400">
                查看复盘（即将开放）
              </button>
            </div>
          </div>
        ) : (
          <div className="border-t border-slate-200 bg-white p-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                  e.preventDefault();
                  void send();
                }
              }}
              rows={3}
              maxLength={2000}
              disabled={sending}
              placeholder="输入你的话，Enter 发送，Shift+Enter 换行"
              className="w-full resize-none rounded-md border border-slate-300 p-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400 disabled:bg-slate-100"
            />
            <div className="mt-2 flex items-center justify-between">
              <button type="button" onClick={finish} className="text-sm text-slate-500 hover:underline">结束演练</button>
              <button
                type="button"
                onClick={() => void send()}
                disabled={sending || !input.trim()}
                className="rounded-md bg-slate-900 px-4 py-1.5 text-sm text-white disabled:bg-slate-300"
              >
                发送
              </button>
            </div>
          </div>
        )}
      </section>

      <aside className="rounded-xl border border-slate-200 bg-white p-4">
        <label className="mb-4 flex items-center justify-between text-sm">
          <span className="font-medium">训练提示</span>
          <input
            type="checkbox"
            checked={hints}
            onChange={(e) => {
              setHints(e.target.checked);
              writeHints(e.target.checked);
            }}
          />
        </label>
        {hints ? (
          <>
            {state && (
              <>
                <Bar label="信任度" value={state.trust} color="bg-emerald-500" />
                <Bar label="耐心" value={state.patience} color="bg-amber-500" />
                <Bar label="兴趣" value={state.engagement} color="bg-sky-500" />
              </>
            )}
            <div className="mt-4 text-xs text-slate-500">上一句的表现</div>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {(lastRep?.signals.length ?? 0) === 0 && <span className="text-xs text-slate-400">暂无明显信号</span>}
              {lastRep?.signals.map((s) => (
                <span
                  key={s}
                  className={`rounded-full px-2 py-0.5 text-xs ${
                    SIGNAL_POLARITY[s] === "good" ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-800"
                  }`}
                >
                  {SIGNAL_LABEL[s]}
                </span>
              ))}
            </div>
          </>
        ) : (
          <p className="text-xs text-slate-400">考核模式：状态与提示已隐藏。</p>
        )}
      </aside>
    </div>
  );
}
