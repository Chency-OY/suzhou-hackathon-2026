import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { DiaryReview, FieldDiary } from "../types";
import { startVoiceInput, voiceInputAvailable } from "../voice";

const message = (error: unknown) => error instanceof Error ? error.message : String(error);

function DigestList({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return <section className="mt-4"><h3 className="text-xs font-bold text-[#176b91]">{title}</h3><ul className="mt-2 list-inside list-disc space-y-1 text-sm leading-6">{items.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ul></section>;
}

function DiaryCard({ item, onDelete }: { item: FieldDiary; onDelete: (id: string) => void }) {
  const [review, setReview] = useState<DiaryReview | null>(null);
  const [reviewBusy, setReviewBusy] = useState(false);
  const [reviewError, setReviewError] = useState("");

  async function runReview() {
    setReviewBusy(true); setReviewError("");
    try { setReview(await api.reviewDiary(item.id)); }
    catch (cause) { setReviewError(message(cause)); }
    finally { setReviewBusy(false); }
  }

  const statusLabel = {
    possible_conflict: "可能与说明书不一致，待人工核对",
    possible_support: "找到相符资料，仍需人工核对",
    insufficient: "资料不足，尚不能判断",
    out_of_scope: "不在本品说明书对照范围",
  };
  return <article className="game-panel p-5 sm:p-6">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><p className="game-kicker">FIELD NOTES / 拜访回忆</p><h2 className="mt-2 text-base font-bold">{item.hospital || "未填医院"}{item.doctor_name ? ` · ${item.doctor_name}` : ""}</h2><p className="game-muted mt-1 text-xs">{new Date(item.created_at).toLocaleString("zh-CN")}</p></div>
      <div className="flex flex-wrap items-center gap-4">{!item.degraded && <Link className="game-link" to={`/home?diary=${encodeURIComponent(item.id)}`}>用这篇日记再练一次 →</Link>}<Link className="game-link" to="/radar">查公开论文 ↗</Link><button className="game-link border-0 bg-transparent" type="button" onClick={() => onDelete(item.id)}>删除这篇</button></div>
    </div>
    {item.degraded && <div className="game-alert mt-4">AI 整理暂不可用，已保存原话，可稍后回看。</div>}
    <p className="mt-5 rounded-lg border border-[#d5e4ed] bg-[#f5f9fc] p-4 text-sm leading-7">{item.digest.summary}</p>
    <DigestList title="当时的第一感受" items={item.digest.first_impressions} />
    <DigestList title="医生明确表达的反馈" items={item.digest.doctor_feedback} />
    <DigestList title="我可以改进的地方" items={item.digest.what_to_improve} />
    <DigestList title="下次拜访前准备" items={item.digest.next_visit} />
    <DigestList title="需要核对的说法" items={item.digest.uncertain_claims} />
    <div className="mt-5 border-t border-[#d5e4ed] pt-4">
      <button className="game-btn game-btn-outline" type="button" disabled={reviewBusy} onClick={() => void runReview()}>{reviewBusy ? "正在对照资料…" : review ? "重新查看资料对照" : "核对日记中的说法 →"}</button>
      {reviewError && <div className="game-alert mt-3" role="alert">{reviewError}</div>}
      {review && <div className="mt-4 space-y-4" role="status">
        <p className="game-muted text-xs leading-6">仅对照本品说明书整理条目；请打开原说明书核对。模型判断只是待复核线索。{review.academic_candidate_count > 0 && `另有 ${review.academic_candidate_count} 条同名论文候选，作者身份未确认，未参与裁定。`}</p>
        {review.findings.length === 0 ? <p className="text-sm">这篇日记没有提取到需要对照的医学说法。</p> : review.findings.map((finding, index) =>
          <section key={`${index}-${finding.claim}`} className="rounded-lg border border-[#d5e4ed] bg-[#f7fafc] p-4">
            <p className="text-sm font-semibold leading-6">{finding.claim}</p>
            <p className="mt-2 text-xs font-bold text-[#176b91]">{statusLabel[finding.status]}</p>
            {finding.evidence_quote && <p className="mt-2 border-l-2 border-[#83bad1] pl-3 text-xs leading-6">资料库条目引用：“{finding.evidence_quote}”</p>}
            {finding.candidates.length > 0 && <details className="mt-3 text-xs"><summary className="game-link cursor-pointer">查看候选资料</summary><ul className="mt-2 space-y-2">{finding.candidates.map((source) => <li key={source.id}><a className="game-link" href={source.url} target="_blank" rel="noreferrer">官方说明书 ↗</a><span className="game-muted ml-2">{source.id}</span><p className="game-muted mt-1 leading-5">{source.excerpt}</p></li>)}</ul></details>}
          </section>)}
      </div>}
    </div>
    <details className="mt-5 border-t border-[#d5e4ed] pt-4"><summary className="game-link cursor-pointer">查看我的原话</summary><p className="mt-3 whitespace-pre-wrap text-sm leading-7">{item.raw_text}</p></details>
    <p className="game-muted mt-4 text-[11px] leading-5">AI 只帮助整理回忆，尚未核实医生观点或医学事实；原话始终保留。</p>
  </article>;
}

export default function DiaryPage() {
  const [hospital, setHospital] = useState("");
  const [doctorName, setDoctorName] = useState("");
  const [rawText, setRawText] = useState("");
  const [items, setItems] = useState<FieldDiary[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [listening, setListening] = useState(false);
  const [error, setError] = useState("");
  const stopVoice = useRef<(() => void) | null>(null);

  useEffect(() => {
    let active = true;
    void api.listDiary().then((data) => { if (active) setItems(data); }).catch((cause) => { if (active) setError(message(cause)); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; stopVoice.current?.(); };
  }, []);

  function toggleVoice() {
    if (listening) { stopVoice.current?.(); setListening(false); return; }
    setError("");
    stopVoice.current?.();
    stopVoice.current = startVoiceInput(
      (text) => setRawText((current) => current ? `${current.trim()}，${text}` : text),
      setError,
      setListening,
    );
  }

  async function save() {
    if (saving || rawText.trim().length < 8) return;
    stopVoice.current?.();
    setListening(false);
    setSaving(true);
    setError("");
    try {
      const item = await api.createDiary({ hospital, doctor_name: doctorName, raw_text: rawText });
      setItems((current) => [item, ...current]);
      setRawText("");
      setHospital("");
      setDoctorName("");
    } catch (cause) { setError(message(cause)); }
    finally { setSaving(false); }
  }

  async function remove(id: string) {
    if (!window.confirm("删除后无法恢复这篇日记，确定删除吗？")) return;
    try { await api.deleteDiary(id); setItems((current) => current.filter((item) => item.id !== id)); }
    catch (cause) { setError(message(cause)); }
  }

  return <div className="mx-auto max-w-4xl">
    <p className="game-kicker">FRONTLINE DIARY / 前线日记本</p>
    <h1 className="game-title mt-2">趁第一感受还清楚，马上说下来</h1>
    <p className="game-muted mt-3 text-sm leading-7">拜访结束后可以分段口述，文字会接在一起。确认原话后，DeepSeek 帮你整理成几条回忆和下次准备；同一账号下次还能回看。</p>

    <section className="game-panel mt-6 p-5 sm:p-7">
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="text-xs font-bold">医院（可选）<input className="game-field mt-2" maxLength={120} value={hospital} onChange={(event) => setHospital(event.target.value)} placeholder="例如：某医院" /></label>
        <label className="text-xs font-bold">医生称呼（可选）<input className="game-field mt-2" maxLength={80} value={doctorName} onChange={(event) => setDoctorName(event.target.value)} placeholder="例如：某主任" /></label>
      </div>
      <label className="mt-5 block text-xs font-bold" htmlFor="diary-raw">我刚才想到的事</label>
      <textarea id="diary-raw" className="game-field mt-2 min-h-[180px] resize-y text-sm leading-7" maxLength={4000} value={rawText} onChange={(event) => setRawText(event.target.value)} placeholder="比如：今天主任明显很赶时间，我一提性价比就被打断了。我应该先问他最担心什么……" />
      <div className="mt-3 flex flex-wrap items-center gap-3">
        {voiceInputAvailable() && <button className="game-btn game-btn-outline" type="button" onClick={toggleVoice} disabled={saving}>{listening ? "正在听，请说话…" : "🎙 语音输入"}</button>}
        <button className="game-btn" type="button" onClick={() => void save()} disabled={saving || rawText.trim().length < 8}>{saving ? "正在整理…" : "保存并整理日记 →"}</button>
      </div>
      <p className="game-muted mt-3 text-[11px] leading-5">先确认识别出的文字再保存。请勿录入真实患者身份、电话或病历信息。</p>
      {error && <div className="game-alert mt-4" role="alert">{error}</div>}
    </section>

    <div className="mb-3 mt-9 flex items-end justify-between"><h2 className="text-lg font-bold">我的拜访回忆</h2><span className="game-muted text-xs">{items.length} 篇</span></div>
    {loading ? <div className="game-panel p-6 text-sm">正在读取日记…</div> : items.length === 0 ? <div className="game-panel p-6 text-sm">还没有日记。下一次拜访结束，先把第一感受记下来。</div> : <div className="space-y-4">{items.map((item) => <DiaryCard key={item.id} item={item} onDelete={(id) => void remove(id)} />)}</div>}
  </div>;
}
