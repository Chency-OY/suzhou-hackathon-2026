import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { currentAccount } from "../auth";
import { groupDiariesByDay, MAX_DIARY_CHARS, readDiaryDraft, saveDiaryDraft } from "../diaryLocal";
import type { AcademicCrosscheck, DiaryDigest, DiaryPreview, DiaryReview, FieldDiary } from "../types";
import { startVoiceInput, voiceInputAvailable } from "../voice";

const message = (error: unknown) => error instanceof Error ? error.message : String(error);

function DiaryPoints({ digest }: { digest: DiaryDigest }) {
  const groups = [
    ["第一感受", digest.first_impressions], ["医生反馈", digest.doctor_feedback],
    ["下次改进", digest.what_to_improve], ["下次准备", digest.next_visit],
    ["待核对", digest.uncertain_claims],
  ] as const;
  const points = groups.flatMap(([label, entries]) => entries.map((entry) => ({ label, entry })));
  return <section className="mt-5"><h3 className="text-sm font-bold">这次拜访的要点</h3>
    {points.length ? <ol className="mt-3 space-y-2">{points.map(({ label, entry }, index) => <li className="flex gap-3 rounded-lg border border-[#d5e4ed] bg-[#f7fafc] p-3 text-sm leading-6" key={`${label}-${index}`}><span className="font-bold text-[#176b91]">{index + 1}.</span><span><strong className="mr-2 text-xs text-[#176b91]">{label}</strong>{entry}</span></li>)}</ol>
      : <p className="game-muted mt-3 text-sm">这次只保留了一句话概括；完整原话仍可展开查看。</p>}</section>;
}

function DiaryCard({ item, onDelete }: { item: FieldDiary; onDelete: (id: string) => void }) {
  const [review, setReview] = useState<DiaryReview | null>(null);
  const [reviewBusy, setReviewBusy] = useState(false);
  const [reviewError, setReviewError] = useState("");
  const [crosscheck, setCrosscheck] = useState<AcademicCrosscheck | null>(null);
  const [crossBusy, setCrossBusy] = useState(false);
  const [crossError, setCrossError] = useState("");

  async function runReview() {
    setReviewBusy(true); setReviewError("");
    try { setReview(await api.reviewDiary(item.id)); }
    catch (cause) { setReviewError(message(cause)); }
    finally { setReviewBusy(false); }
  }

  async function runCrosscheck() {
    setCrossBusy(true); setCrossError("");
    try { setCrosscheck(await api.crosscheckDiaryAcademic(item.id)); }
    catch (cause) { setCrossError(message(cause)); }
    finally { setCrossBusy(false); }
  }

  const radarLink = item.doctor_name && item.hospital
    ? `/radar?${new URLSearchParams({ doctor_name: item.doctor_name, hospital: item.hospital })}` : "/radar";

  const statusLabel = {
    possible_conflict: "可能与说明书不一致，待人工核对",
    possible_support: "找到相符资料，仍需人工核对",
    insufficient: "资料不足，尚不能判断",
    out_of_scope: "不在本品说明书对照范围",
  };
  return <article id={`diary-${item.id}`} className="game-panel scroll-mt-4 p-5 sm:p-6">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><p className="game-kicker">FIELD NOTES / 拜访回忆</p><h2 className="mt-2 text-base font-bold">{item.hospital || "拜访随记"}{item.doctor_name ? ` · ${item.doctor_name}` : ""}</h2><p className="game-muted mt-1 text-xs">{new Date(item.created_at).toLocaleString("zh-CN")}</p></div>
      <div className="flex flex-wrap items-center gap-4">{!item.degraded && <Link className="game-link" to={`/home?diary=${encodeURIComponent(item.id)}`}>用这篇日记再练一次 →</Link>}<Link className="game-link" to={radarLink}>查公开学术资料 ↗</Link><button className="game-link border-0 bg-transparent" type="button" onClick={() => onDelete(item.id)}>删除这篇</button></div>
    </div>
    <div className="mt-5 border-t border-[#d5e4ed] pt-4">
      <button className="game-btn game-btn-outline" type="button" disabled={crossBusy || !item.doctor_name || !item.hospital} onClick={() => void runCrosscheck()}>{crossBusy ? "正在交叉核对…" : "对照日记与学术雷达 →"}</button>
      {(!item.doctor_name || !item.hospital) && <p className="game-muted mt-2 text-xs">原话里没有可确认的医生姓名和医院，暂时无法对照同名学术线索。</p>}
      {crossError && <div className="game-alert mt-3" role="alert">{crossError}</div>}
      {crosscheck && <div className="mt-4 rounded-lg border border-[#d5e4ed] bg-[#f7fafc] p-4" role="status"><p className="text-xs leading-6">{crosscheck.note}</p>{crosscheck.status === "no_radar" && <Link className="game-link mt-2 inline-block text-xs" to={radarLink}>先手动搜索学术资料 →</Link>}{crosscheck.tensions.map((tension, index) => <div className="mt-4 border-t border-[#d5e4ed] pt-4 text-xs leading-6" key={`${tension.source_id}-${index}`}><p><strong>日记原话：</strong>“{tension.diary_quote}”</p><p className="mt-2"><strong>网页摘录：</strong>“{tension.source_quote}”</p><a className="game-link mt-2 inline-block" href={tension.source_url} target="_blank" rel="noreferrer">打开候选来源：{tension.source_title} ↗</a><p className="game-muted mt-2">{tension.note}</p></div>)}</div>}
      <p className="game-muted mt-3 text-[11px] leading-5">仅核对学术活动原话；同名身份未确认，不会把网页线索自动写入模拟医生画像。</p>
    </div>
    {item.degraded && <div className="game-alert mt-4">AI 整理暂不可用，已保存原话，可稍后回看。</div>}
    <div className="mt-5 rounded-lg border border-[#d5e4ed] bg-[#f5f9fc] p-4"><p className="game-kicker">AI 整理要点</p><p className="mt-2 text-sm leading-7">{item.digest.summary}</p></div>
    <DiaryPoints digest={item.digest} />
    <div className="mt-5 border-t border-[#d5e4ed] pt-4">
      <button className="game-btn game-btn-outline" type="button" disabled={reviewBusy} onClick={() => void runReview()}>{reviewBusy ? "正在对照资料…" : review ? "重新查看资料对照" : "核对日记中的说法 →"}</button>
      {reviewError && <div className="game-alert mt-3" role="alert">{reviewError}</div>}
      {review && <div className="mt-4 space-y-4" role="status">
        <p className="game-muted text-xs leading-6">仅对照本品说明书整理条目；请打开原说明书核对。模型判断只是待复核线索。{review.academic_candidate_count > 0 && `另有 ${review.academic_candidate_count} 条同名论文候选，作者身份未确认，未参与裁定。`}</p>
        {review.findings.length === 0 ? <p className="text-sm">这篇日记没有提取到需要对照的医学说法。</p> : review.findings.map((finding, index) =>
          <section key={`${index}-${finding.claim}`} className="rounded-lg border border-[#d5e4ed] bg-[#f7fafc] p-4">
            <p className="text-sm font-semibold leading-6">{finding.claim}</p>
            <p className="mt-2 text-xs font-bold text-[#176b91]">{statusLabel[finding.status]}</p>
            {finding.note && <p className="game-muted mt-2 text-xs leading-6">{finding.note}</p>}
            {finding.evidence_quote && <p className="mt-2 border-l-2 border-[#83bad1] pl-3 text-xs leading-6">资料库条目引用：“{finding.evidence_quote}”</p>}
            {finding.candidates.length > 0 && <details className="mt-3 text-xs"><summary className="game-link cursor-pointer">查看候选资料</summary><ul className="mt-2 space-y-2">{finding.candidates.map((source) => <li key={source.id}><a className="game-link" href={source.url} target="_blank" rel="noreferrer">官方说明书 ↗</a><span className="game-muted ml-2">{source.id}</span><p className="game-muted mt-1 leading-5">{source.excerpt}</p></li>)}</ul></details>}
          </section>)}
      </div>}
    </div>
    <details className="mt-5 border-t border-[#d5e4ed] pt-4"><summary className="game-link cursor-pointer">查看完整识别原文 · {item.raw_text.length} 字</summary><p className="mt-3 whitespace-pre-wrap break-words text-sm leading-7">{item.raw_text}</p></details>
    <p className="game-muted mt-4 text-[11px] leading-5">AI 只帮助整理回忆，尚未核实医生观点或医学事实；原话始终保留。</p>
  </article>;
}

export default function DiaryPage() {
  const [rawText, setRawText] = useState("");
  const [items, setItems] = useState<FieldDiary[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [listening, setListening] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [error, setError] = useState("");
  const [isGuest, setIsGuest] = useState(false);
  const [preview, setPreview] = useState<DiaryPreview | null>(null);
  const [latestId, setLatestId] = useState("");
  const [draftAccountId, setDraftAccountId] = useState<string | null>(null);
  const stopVoice = useRef<(() => void) | null>(null);
  const pendingSave = useRef(false);
  const saveInFlight = useRef(false);
  const rawTextRef = useRef("");

  useEffect(() => {
    let active = true;
    void currentAccount().then((account) => account?.is_guest ? [] : api.listDiary())
      .then((data) => { if (active) setItems(data); })
      .catch((cause) => { if (active) setError(message(cause)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; pendingSave.current = false; stopVoice.current?.(); };
  }, []);

  useEffect(() => {
    let active = true;
    void currentAccount().then((account) => {
      if (!active || !account) return;
      setIsGuest(account.is_guest);
      const draft = readDiaryDraft(account.id);
      if (draft) {
        rawTextRef.current = draft.rawText;
        setRawText(draft.rawText);
      }
      setDraftAccountId(account.id);
    }).catch(() => {});
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (draftAccountId) saveDiaryDraft(draftAccountId, { hospital: "", doctorName: "", rawText });
  }, [draftAccountId, rawText]);

  useEffect(() => {
    if (latestId) document.getElementById(`diary-${latestId}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [latestId]);

  useEffect(() => {
    if (preview) document.getElementById("diary-preview")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [preview]);

  function changeRawText(value: string) {
    rawTextRef.current = value;
    setRawText(value);
  }

  function toggleVoice() {
    if (listening) {
      pendingSave.current = true;
      setStopping(true);
      stopVoice.current?.();
      return;
    }
    setError("");
    stopVoice.current?.();
    stopVoice.current = startVoiceInput(
      (text) => changeRawText(rawTextRef.current ? `${rawTextRef.current.trim()}，${text}` : text),
      (message) => { pendingSave.current = false; setStopping(false); setError(message); },
      (active) => {
        setListening(active);
        if (!active) {
          setStopping(false);
          if (pendingSave.current) { pendingSave.current = false; void save(); }
        }
      },
    );
  }

  async function save() {
    if (saveInFlight.current) return;
    const transcript = rawTextRef.current.trim();
    if (transcript.length < 8) { setError("请再说几句，至少记录 8 个字后才能整理。"); return; }
    if (transcript.length > MAX_DIARY_CHARS) { setError("单篇内容已超过上限，请分成两篇记录。"); return; }
    saveInFlight.current = true;
    setSaving(true);
    setError("");
    try {
      const account = await currentAccount();
      if (!account) throw new Error("请先开始试用或登录，再整理口述。");
      if (account.is_guest) {
        setIsGuest(true);
        setPreview(await api.previewDiary(transcript));
        return;
      }
      const item = await api.createDiary({ hospital: "", doctor_name: "", raw_text: transcript });
      setIsGuest(false);
      setPreview(null);
      setItems((current) => [item, ...current]);
      setLatestId(item.id);
      changeRawText("");
    } catch (cause) { setError(message(cause)); }
    finally { saveInFlight.current = false; setSaving(false); }
  }

  async function remove(id: string) {
    if (!window.confirm("删除后无法恢复这篇日记，确定删除吗？")) return;
    try { await api.deleteDiary(id); setItems((current) => current.filter((item) => item.id !== id)); }
    catch (cause) { setError(message(cause)); }
  }

  return <div className="mx-auto max-w-4xl">
    <p className="game-kicker">FRONTLINE DIARY / 前线日记本</p>
    <h1 className="game-title mt-2">趁第一感受还清楚，马上说下来</h1>
    <p className="game-muted mt-3 text-sm leading-7">点一下开始说，想到什么就直接讲；再点一下结束，系统会自动保存原话，把感受和下一步整理成一条条要点。医生姓名、医院无需手填。</p>

    <section className="game-panel mt-6 p-5 sm:p-7">
      <div className="flex flex-col items-center text-center">
        <button className={`grid h-32 w-32 place-items-center rounded-full text-base font-bold shadow-[0_16px_40px_#176b9133] transition-transform active:scale-95 ${listening ? "bg-[#d45555] text-white" : "bg-[#176b91] text-white"}`} type="button"
          onClick={toggleVoice} disabled={!voiceInputAvailable() || saving || stopping} aria-pressed={listening}
          aria-label={listening ? "停止录音并自动整理" : "开始语音记录"}>
          <span className="flex flex-col items-center gap-1"><span className="text-3xl" aria-hidden="true">{listening ? "■" : "🎙"}</span>{stopping ? "正在结束…" : saving ? "正在整理…" : listening ? "结束并整理" : "点一下开讲"}</span>
        </button>
        <p className="game-muted mt-4 text-xs leading-6" role="status">{stopping ? "正在接收最后一段语音，请稍等…" : saving ? "正在整理并保存，请稍等…" : listening ? "正在连续记录，只有你点结束才会提交。" : "说完后再点一次，系统就会整理成要点。"}</p>
        {rawText && <p className="game-muted mt-2 text-xs">已记下 {rawText.length.toLocaleString("zh-CN")} 字；原话草稿保存在这台设备。</p>}
      </div>
      {!voiceInputAvailable() && <p className="game-alert mt-4 text-xs">当前设备没有可用的语音识别服务，可在下方输入原话。</p>}
      {(rawText || !voiceInputAvailable()) && <details className="mt-5 border-t border-[#d5e4ed] pt-4" open={!voiceInputAvailable()}>
        <summary className="game-link cursor-pointer text-xs">查看或修正识别原话（可选）</summary>
        <label className="mt-3 block text-xs font-bold" htmlFor="diary-raw">识别原话</label>
        <textarea id="diary-raw" className="game-field mt-2 min-h-[120px] resize-y text-sm leading-7" maxLength={MAX_DIARY_CHARS} disabled={saving || listening || stopping} value={rawText} onChange={(event) => changeRawText(event.target.value)} placeholder="把刚才的感受说出来；语音不可用时也可以在这里输入。" />
        {!listening && !saving && !stopping && rawText.trim().length >= 8 && <button className="game-btn game-btn-outline mt-3" type="button" onClick={() => void save()}>整理这份草稿 →</button>}
      </details>}
      <p className="game-muted mt-4 text-[11px] leading-5">请勿录入患者姓名、手机号、身份证号或病历信息；明显的联系方式和身份证号会在保存前拦截。姓名和医院只会从你明确说出的原话中提取。</p>
      {error && <div className="game-alert mt-4" role="alert">{error}</div>}
    </section>

    {preview && <section id="diary-preview" className="game-panel mt-5 scroll-mt-4 p-5 sm:p-7" role="status">
      <p className="game-kicker">试用整理结果 · 尚未保存</p>
      <h2 className="mt-2 text-lg font-bold">{preview.hospital || "这次拜访"}{preview.doctor_name ? ` · ${preview.doctor_name}` : ""}</h2>
      <p className="game-muted mt-2 text-sm leading-7">{preview.digest.summary}</p>
      {preview.degraded && <p className="game-alert mt-3 text-xs">AI 暂不可用，原话仍保存在本机草稿。</p>}
      <DiaryPoints digest={preview.digest} />
      <details className="mt-4 border-t border-[#d5e4ed] pt-3"><summary className="game-link cursor-pointer text-xs">查看完整原话</summary><p className="mt-3 whitespace-pre-wrap break-words text-sm leading-7">{preview.raw_text}</p></details>
      <p className="game-muted mt-4 text-xs leading-6">这是临时预览，服务器没有保存日记。创建账号后，再点“整理这份草稿”即可保存。</p>
    </section>}

    {!isGuest && <><div className="mb-3 mt-9 flex items-end justify-between"><h2 className="text-lg font-bold">每天的拜访回忆</h2><span className="game-muted text-xs">{items.length} 篇</span></div>
      {loading ? <div className="game-panel p-6 text-sm">正在读取日记…</div> : items.length === 0 ? <div className="game-panel p-6 text-sm">还没有日记。下一次拜访结束，先把第一感受记下来。</div> : <div className="space-y-8">{groupDiariesByDay(items).map((day) => <section key={day.key} aria-label={day.label}><div className="mb-3 flex items-center justify-between border-b border-[#d5e4ed] pb-2"><h3 className="text-sm font-bold">{day.label}</h3><span className="game-muted text-xs">{day.items.length} 篇</span></div><div className="space-y-4">{day.items.map((item) => <DiaryCard key={item.id} item={item} onDelete={(id) => void remove(id)} />)}</div></section>)}</div>}</>}
  </div>;
}
