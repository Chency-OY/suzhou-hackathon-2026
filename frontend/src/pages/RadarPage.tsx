import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { radarRefreshDue } from "../radarLocal";
import type { AcademicRadar } from "../types";

const errorText = (error: unknown) => error instanceof Error ? error.message : String(error);
const kindLabel = { paper: "论文", conference: "会议", talk: "演讲" };

function RadarCard({ result, onToggle, onRefresh, switching, refreshing }: { result: AcademicRadar; onToggle: (item: AcademicRadar) => void; onRefresh: (item: AcademicRadar) => void; switching: boolean; refreshing: boolean }) {
  const sources = result.web_sources || [];
  const points = result.answer_points || [];
  const recent = Date.now() - Date.parse(result.searched_at) < 24 * 60 * 60 * 1000;
  const sourceById = new Map(sources.map((source) => [source.id, source]));
  return <article className="game-panel p-5 sm:p-6">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><p className="game-kicker">PUBLIC RESEARCH / 公开学术资料</p>
        <h2 className="mt-2 text-base font-bold">{result.doctor_name} · {result.hospital}</h2>
        <p className="game-muted mt-1 text-xs">检索姓名：{result.search_name} · {new Date(result.searched_at).toLocaleString("zh-CN")}</p></div>
      <span className="rounded-full border border-[#b9d5e3] px-3 py-1 text-xs text-[#176b91]">{sources.length} 条网页候选 · {result.works.length} 条论文索引</span>
    </div>
    <div className="mt-4 flex flex-wrap items-center gap-3 border-b border-[#d5e4ed] pb-4 text-xs">
      <span className={result.auto_refresh ? "font-bold text-[#176b91]" : "game-muted"}>{result.auto_refresh ? "打开页面时自动更新 · 已开启" : "打开页面时自动更新 · 已关闭"}</span>
      <button className="game-link border-0 bg-transparent" type="button" disabled={switching} onClick={() => onToggle(result)}>{switching ? "正在保存…" : result.auto_refresh ? "关闭自动更新" : "开启自动更新"}</button>
      {result.last_auto_checked_at && <span className="game-muted">最近自动检查：{new Date(result.last_auto_checked_at).toLocaleString("zh-CN")}</span>}
    </div>
    {result.refresh_error && <div className="game-alert mt-4" role="status">{result.refresh_error}</div>}
    {points.length > 0 && <div className="mt-4 flex flex-wrap items-center gap-3">{recent
      ? <Link className="game-btn" to={`/home?radar=${encodeURIComponent(result.id)}`}>用公开学术线索练一次 →</Link>
      : <button className="game-btn" type="button" disabled={switching || refreshing} onClick={() => onRefresh(result)}>{refreshing ? "正在更新…" : "更新资料后再练 →"}</button>}
      <span className="game-muted text-xs">只练证据表达，不扮演真实医生</span></div>}
    {result.institution_name && <p className="game-muted mt-4 text-xs">索引中的医院：<a className="game-link" href={result.institution_url} target="_blank" rel="noreferrer">{result.institution_name} ↗</a></p>}
    <p className="game-alert mt-4" role="status">{result.note}</p>
    {points.length > 0 && <section className="mt-5 rounded-lg border border-[#c8dfe9] bg-[#f2f9fc] p-4">
      <h3 className="text-sm font-bold">AI 整理的公开资料线索</h3>
      <p className="game-muted mt-1 text-xs leading-5">每条摘录来自下方链接；同名身份仍待人工确认，不能视为完整学术履历。</p>
      <ol className="mt-3 space-y-4">{points.map((point, index) => {
        const source = sourceById.get(point.source_id);
        return <li key={`${point.source_id}-${index}`} className="border-t border-[#d5e4ed] pt-3 text-sm leading-6">
          <span className="mr-2 rounded bg-[#dceff8] px-2 py-1 text-[11px] text-[#176b91]">{kindLabel[point.kind]}</span>{point.statement}
          {source && <p className="game-muted mt-2 text-xs">来源摘录：“{point.evidence_quote}” · <a className="game-link" href={source.url} target="_blank" rel="noreferrer">打开原网页 ↗</a></p>}
        </li>;
      })}</ol>
    </section>}
    {sources.length > 0 && <details className="mt-5"><summary className="game-link cursor-pointer">查看 {sources.length} 条实时网页候选</summary>
      <ul className="mt-3 space-y-3">{sources.map((source) => <li key={source.id} className="rounded-lg border border-[#d5e4ed] bg-[#f7fafc] p-4">
        <a className="game-link text-sm font-bold" href={source.url} target="_blank" rel="noreferrer">{source.title} ↗</a>
        <p className="game-muted mt-2 text-xs">{kindLabel[source.kind]} · {source.site_name || "公开网页"}{source.published_at && ` · ${source.published_at.slice(0, 10)}`}</p>
        {source.snippet && <p className="mt-2 text-xs leading-6">{source.snippet}</p>}
        <p className="mt-2 text-[11px] text-[#9b5a29]">{source.name_in_source && source.hospital_in_source ? "姓名与医院同时出现，身份仍待确认" : "检索候选，尚未找到姓名与医院同时出现的依据"}</p>
      </li>)}</ul>
    </details>}
    {result.works.length > 0 && <ol className="mt-4 space-y-3">{result.works.map((work) =>
      <li key={work.id} className="rounded-lg border border-[#d5e4ed] bg-[#f7fafc] p-4">
        <a className="game-link text-sm font-bold leading-6" href={work.url} target="_blank" rel="noreferrer">{work.title} ↗</a>
        <p className="game-muted mt-2 text-xs leading-5">{work.publication_date || "日期未列"} · {work.journal || "期刊未列"} · {work.author_name} · {work.affiliation}</p>
        <p className="mt-2 text-[11px] text-[#9b5a29]">同名候选，医生身份待确认</p>
      </li>)}</ol>}
  </article>;
}

export default function RadarPage() {
  const [doctorName, setDoctorName] = useState(() => new URLSearchParams(window.location.search).get("doctor_name") || "");
  const [hospital, setHospital] = useState(() => new URLSearchParams(window.location.search).get("hospital") || "");
  const [results, setResults] = useState<AcademicRadar[]>([]);
  const [busy, setBusy] = useState(false);
  const [autoBusy, setAutoBusy] = useState(false);
  const [switchingId, setSwitchingId] = useState("");
  const [refreshingId, setRefreshingId] = useState("");
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    void api.listRadar().then(async (items) => {
      if (!active) return;
      setResults(items);
      if (!items.some((item) => radarRefreshDue(item))) return;
      setAutoBusy(true);
      try {
        const updated = await api.refreshDueRadar();
        if (active) setResults((current) => mergeRadar(current, updated));
      } catch (cause) { if (active) setError(`自动更新暂不可用：${errorText(cause)}`); }
      finally { if (active) setAutoBusy(false); }
    }).catch((cause) => { if (active) setError(errorText(cause)); });
    return () => { active = false; };
  }, []);

  async function toggleAutoRefresh(item: AcademicRadar) {
    if (switchingId || autoBusy) return;
    setSwitchingId(item.id); setError("");
    try {
      const updated = await api.setRadarAutoRefresh(item.id, !item.auto_refresh);
      setResults((current) => mergeRadar(current, [updated]));
      if (updated.auto_refresh && radarRefreshDue(updated)) {
        setAutoBusy(true);
        const refreshed = await api.refreshDueRadar();
        setResults((current) => mergeRadar(current, refreshed));
      }
    } catch (cause) { setError(errorText(cause)); }
    finally { setSwitchingId(""); setAutoBusy(false); }
  }

  async function refreshForPractice(item: AcademicRadar) {
    if (refreshingId || autoBusy) return;
    setRefreshingId(item.id); setError("");
    try { const updated = await api.searchRadar(item.doctor_name, item.hospital, true); setResults((current) => mergeRadar(current, [updated])); }
    catch (cause) { setError(errorText(cause)); }
    finally { setRefreshingId(""); }
  }

  async function search() {
    if (busy || doctorName.trim().length < 2 || hospital.trim().length < 4) return;
    setBusy(true); setError("");
    try {
      const result = await api.searchRadar(doctorName.trim(), hospital.trim(), false, autoRefresh ? true : undefined);
      setResults((current) => mergeRadar(current, [result]));
    } catch (cause) { setError(errorText(cause)); }
    finally { setBusy(false); }
  }

  return <div className="mx-auto max-w-4xl">
    <p className="game-kicker">ACADEMIC RADAR / 学术雷达</p>
    <h1 className="game-title mt-2">输入医院与姓名，查公开学术资料</h1>
    <p className="game-muted mt-3 text-sm leading-7">实时搜索论文、会议和演讲网页，由 AI 整理带来源的回答；论文索引补充候选。结果不保证齐全，同名作者可能混淆，请打开原文核对，候选记录不会直接进入医生画像。</p>
    <section className="game-panel mt-6 p-5 sm:p-7">
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="text-xs font-bold">医生姓名<input className="game-field mt-2" type="text" lang="zh-CN" inputMode="text" autoComplete="name" value={doctorName} maxLength={80} onChange={(event) => setDoctorName(event.target.value)} placeholder="例如：张伟" /></label>
        <label className="text-xs font-bold">医院正式名称<input className="game-field mt-2" type="text" lang="zh-CN" inputMode="text" value={hospital} maxLength={120} onChange={(event) => setHospital(event.target.value)} placeholder="例如：苏州大学附属第一医院" /></label>
      </div>
      <label className="mt-4 flex items-start gap-2 text-xs leading-6"><input className="mt-1" type="checkbox" checked={autoRefresh} onChange={(event) => setAutoRefresh(event.target.checked)} /><span>以后打开雷达页时自动更新这组检索词。每次间隔至少 24 小时；开启后，姓名和医院会再次发送给第三方 AI 检索服务与公开论文索引。随时可在结果卡片关闭。</span></label>
      <button className="game-btn mt-5" type="button" disabled={busy || doctorName.trim().length < 2 || hospital.trim().length < 4} onClick={() => void search()}>{busy ? "正在检索…" : "查询公开资料 →"}</button>
      {error && <div className="game-alert mt-4" role="alert">{error}</div>}
    </section>
    {autoBusy && <p className="game-muted mt-5 text-xs" role="status">正在更新已开启的学术雷达…</p>}
    <div className="mt-8 space-y-4">{results.map((result) => <RadarCard key={result.id} result={result} switching={!!switchingId || autoBusy} refreshing={refreshingId === result.id} onToggle={(item) => void toggleAutoRefresh(item)} onRefresh={(item) => void refreshForPractice(item)} />)}</div>
  </div>;
}

function mergeRadar(current: AcademicRadar[], incoming: AcademicRadar[]): AcademicRadar[] {
  const merged = new Map(current.map((item) => [item.id, item]));
  for (const item of incoming) merged.set(item.id, item);
  return [...merged.values()].sort((a, b) => Date.parse(b.searched_at) - Date.parse(a.searched_at));
}
