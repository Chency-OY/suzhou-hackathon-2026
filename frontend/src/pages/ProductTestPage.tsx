import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { useAsync } from "../hooks";
import type { ProductCheckResult } from "../types";
import { startVoiceInput, voiceInputAvailable } from "../voice";

const questions = [
  { id: "mechanism", title: "作用靶点与药物类型", prompt: "这款产品的作用靶点或通路是什么？它属于哪一类药物？" },
  { id: "scope", title: "当前阶段与主要领域", prompt: "它目前处于什么阶段？主要用于或研究什么疾病领域？" },
  { id: "boundary", title: "回答资料边界", prompt: "医生问到具体风险或尚未核对的适应症时，你会怎样回答？" },
] as const;

export default function ProductTestPage() {
  const { id = "" } = useParams();
  const { data, error: loadError, loading } = useAsync(() => api.listProducts(), []);
  const product = data?.find((entry) => entry.id === id);
  const [step, setStep] = useState(0);
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState<ProductCheckResult | null>(null);
  const [error, setError] = useState("");
  const [listening, setListening] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [busy, setBusy] = useState(false);
  const answerRef = useRef("");
  const pendingCheck = useRef(false);
  const stopVoice = useRef<(() => void) | null>(null);
  const inFlight = useRef(false);
  const question = questions[step];

  useEffect(() => () => { pendingCheck.current = false; stopVoice.current?.(); }, []);

  function changeAnswer(text: string) {
    answerRef.current = text;
    setAnswer(text);
  }

  async function check() {
    if (!product || inFlight.current) return;
    const spoken = answerRef.current.trim();
    if (spoken.length < 8) { setError("请再说几句，至少回答 8 个字。"); return; }
    inFlight.current = true;
    setBusy(true);
    setError("");
    try { setResult(await api.checkProductAnswer(product.id, question.id, spoken)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "判断暂不可用，请稍后重试。"); }
    finally { inFlight.current = false; setBusy(false); }
  }

  function toggleVoice() {
    if (listening) {
      pendingCheck.current = true;
      setStopping(true);
      stopVoice.current?.();
      return;
    }
    setError("");
    stopVoice.current = startVoiceInput(
      (text) => changeAnswer(answerRef.current ? `${answerRef.current.trim()}，${text}` : text),
      (reason) => { pendingCheck.current = false; setStopping(false); setError(reason); },
      (active) => {
        setListening(active);
        if (!active) {
          setStopping(false);
          if (pendingCheck.current) { pendingCheck.current = false; void check(); }
        }
      },
    );
  }

  function selectStep(index: number) {
    if (listening || stopping || busy) return;
    setStep(index);
    changeAnswer("");
    setResult(null);
    setError("");
  }

  if (loading) return <div className="game-panel p-6">正在读取产品资料…</div>;
  if (loadError || !product) return <div className="game-alert">没有找到这款产品。<Link className="game-link ml-2" to="/products">返回产品目录</Link></div>;

  return <div className="mx-auto max-w-4xl">
    <Link className="game-link text-xs" to="/products">← 返回产品目录</Link>
    <section className="mt-4 rounded-2xl border border-[#c9e3ec] bg-gradient-to-br from-[#f8fcff] via-white to-[#e8f5f8] p-6 text-[#163d5a] shadow-[0_15px_45px_#23465712] sm:p-8">
      <p className="text-[11px] font-extrabold tracking-[.17em] text-[#176b91]">PRODUCT FOCUS / 单品专项测试</p>
      <h1 className="mt-2 text-3xl font-black">{product.name}<span className="ml-3 text-sm font-normal text-[#587083]">{product.generic_name}</span></h1>
      <p className="mt-4 max-w-2xl text-sm leading-7">只练这一款产品的基础资料与表达边界。你可以直接口述回答；结束录音后，AI 会根据已核对资料给出判断。</p>
      <div className="mt-4 flex flex-wrap gap-2 text-xs"><span className="rounded-full bg-[#dff1f6] px-3 py-1.5">{product.stage === "marketed" ? "已上市" : product.stage === "nda_review" ? "上市申请审评中" : "关键临床阶段"}</span><span className="rounded-full bg-[#edf3f5] px-3 py-1.5">{product.area}</span></div>
    </section>

    <div className="mt-6 grid gap-2 sm:grid-cols-3" role="tablist" aria-label="专项测试题目">{questions.map((entry, index) => <button type="button" role="tab" aria-selected={step === index} key={entry.id} onClick={() => selectStep(index)} className={`rounded-xl border px-4 py-3 text-left text-xs font-bold ${step === index ? "border-[#176b91] bg-[#176b91] text-white" : "border-[#d7e5eb] bg-white text-[#31516a]"}`}><span className="mr-2 opacity-70">0{index + 1}</span>{entry.title}</button>)}</div>

    <section className="mt-4 rounded-2xl border border-[#d7e5eb] bg-white p-6 text-[#183b53] shadow-[0_15px_45px_#2346570d] sm:p-8">
      <p className="text-xs font-bold text-[#176b91]">第 {step + 1} 题 / 共 {questions.length} 题</p>
      <h2 className="mt-2 text-xl font-extrabold leading-8">{question.prompt}</h2>
      <div className="mt-6 flex flex-wrap items-center gap-4">
        <button className={`grid h-24 w-24 place-items-center rounded-full text-center text-xs font-bold text-white shadow-[0_12px_30px_#176b9130] ${listening ? "bg-[#d45555]" : "bg-[#176b91]"}`} type="button" onClick={toggleVoice} disabled={!voiceInputAvailable() || stopping || busy} aria-label={listening ? "结束回答并判断" : "开始语音回答"} aria-pressed={listening}><span><span className="block text-2xl">{listening ? "■" : "🎙"}</span>{listening ? "结束并判断" : "语音回答"}</span></button>
        <p className="max-w-sm text-xs leading-6 text-[#60798b]" role="status">{stopping ? "正在接收最后一段语音…" : busy ? "正在核对回答…" : listening ? "持续记录中，点结束后自动判断。" : "点一下开始说，再点一下结束；也可以在下方输入。"}</p>
      </div>
      <label className="mt-6 block text-xs font-bold" htmlFor="product-answer">我的回答</label>
      <textarea id="product-answer" className="game-field mt-2 min-h-[120px] resize-y text-sm leading-7" lang="zh-CN" maxLength={1500} disabled={listening || stopping || busy} value={answer} onChange={(event) => changeAnswer(event.target.value)} placeholder="说出你现在对这款产品的理解…" />
      <div className="mt-4 flex flex-wrap items-center gap-3"><button className="game-btn" type="button" onClick={() => void check()} disabled={listening || stopping || busy}>提交回答，查看 AI 判断 →</button><span className="text-xs text-[#71889a]">仅供学习练习，不用于医学或合规裁定</span></div>
      {error && <div className="game-alert mt-4" role="alert">{error}</div>}
      {result && <div className="mt-6 rounded-xl border border-[#cfe1e9] bg-[#f7fbfd] p-5" role="status"><p className="text-sm font-extrabold text-[#176b91]">{result.status === "correct" ? "要点基本准确" : result.status === "partial" ? "还可补充" : result.status === "incorrect" ? "需要重新核对" : "暂未判断"}</p><p className="mt-2 text-sm leading-7">{result.feedback}</p><p className="mt-4 border-t border-[#d9e8ef] pt-3 text-xs font-bold">已核对的参考要点</p><p className="mt-2 text-sm leading-7">{result.reference}</p><a className="mt-3 inline-block text-xs text-[#176b91] underline underline-offset-2" href={result.source_url} target="_blank" rel="noreferrer">核对原始资料 ↗</a></div>}
      {result && step < questions.length - 1 && <button className="game-btn game-btn-outline mt-5" type="button" onClick={() => selectStep(step + 1)}>下一题 →</button>}
    </section>
    <p className="mt-5 text-xs leading-6 text-[#8196a3]">请勿输入患者身份信息。资料概览来自公司公开报告；已上市产品的完整适应症、用法、不良反应仍需核对现行说明书。</p>
  </div>;
}
