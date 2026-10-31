import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAsync } from "../hooks";
import type { ProductPortfolioItem } from "../types";

type View = "marketed" | "pipeline";

function ProductCard({ item }: { item: ProductPortfolioItem }) {
  const marketed = item.stage === "marketed";
  const program = item.id === "xinermei" ? "xinermei" : "general";
  const stage = item.stage === "nda_review" ? "上市申请审评中" : item.stage === "pivotal" ? "关键临床阶段" : "已上市";
  return <article className="rounded-2xl border border-[#d8e6ee] bg-white p-5 shadow-[0_12px_30px_#2944580d]">
    <div className="flex items-start justify-between gap-3"><div><h3 className="text-lg font-extrabold text-[#163d5a]">{item.name}</h3><p className="mt-1 text-xs leading-5 text-[#587083]">{item.generic_name}</p></div><span className={`shrink-0 rounded-full px-2.5 py-1 text-[10px] font-bold ${marketed ? "bg-[#e6f6ef] text-[#146a50]" : "bg-[#fff3dc] text-[#8b5b12]"}`}>{stage}</span></div>
    <p className="mt-4 min-h-[42px] text-xs leading-6 text-[#475f72]">{item.note}</p>
    <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-[#e4edf2] pt-3 text-[11px]"><span className="text-[#6d8494]">核对日期 {item.checked_on}</span><a className="font-bold text-[#176b91] underline-offset-2 hover:underline" href={item.source_url} target="_blank" rel="noreferrer">查看官方资料 ↗</a></div>
    {marketed && <Link className="mt-4 inline-flex text-xs font-bold text-[#176b91]" to={`/home?program=${program}`}>{item.id === "xinermei" ? "进入信尔美专项训练" : "练习通用沟通"} →</Link>}
  </article>;
}

export default function ProductsPage() {
  const { data, error, loading } = useAsync(() => api.listProducts(), []);
  const [view, setView] = useState<View>("marketed");
  const [query, setQuery] = useState("");
  const marketedCount = data?.filter((item) => item.stage === "marketed").length ?? 0;
  const pipelineCount = data?.length ? data.length - marketedCount : 0;
  const shown = data?.filter((item) => (view === "marketed" ? item.stage === "marketed" : item.stage !== "marketed")
    && `${item.name} ${item.generic_name} ${item.id}`.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase())) ?? [];

  return <div className="mx-auto max-w-5xl">
    <p className="game-kicker">INNOVENT PORTFOLIO / 产品状态</p>
    <h1 className="game-title mt-2">信达产品目录</h1>
    <p className="game-muted mt-3 max-w-3xl text-sm leading-7">按信达公开资料整理已商业化产品和后期研发项目。每张卡片附官方来源与核对日期；研发项目仍未获批，不能作为上市产品介绍，上市时间也尚不确定。</p>
    <div className="mt-6 flex flex-wrap items-center gap-2" role="tablist" aria-label="产品阶段">
      <button role="tab" aria-selected={view === "marketed"} className={`rounded-full px-4 py-2 text-xs font-bold ${view === "marketed" ? "bg-[#176b91] text-white" : "bg-white text-[#446173]"}`} type="button" onClick={() => setView("marketed")}>已上市 · {marketedCount}</button>
      <button role="tab" aria-selected={view === "pipeline"} className={`rounded-full px-4 py-2 text-xs font-bold ${view === "pipeline" ? "bg-[#176b91] text-white" : "bg-white text-[#446173]"}`} type="button" onClick={() => setView("pipeline")}>上市前项目 · {pipelineCount}</button>
    </div>
    <label className="mt-5 block max-w-md text-xs font-bold text-[#446173]">搜索名称或研发编号<input className="game-field mt-2" type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="例如：信尔美、IBI343" /></label>
    {loading && <div className="game-panel mt-5 p-6 text-sm">正在读取产品目录…</div>}
    {error && <div className="game-alert mt-5" role="alert">产品目录加载失败：{error}</div>}
    {!loading && !error && shown.length === 0 && <div className="game-panel mt-5 p-6 text-sm">没有符合条件的产品。</div>}
    <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{shown.map((item) => <ProductCard key={item.id} item={item} />)}</div>
    <p className="game-muted mt-7 text-xs leading-6">目前只有信尔美具备已核对资料的专项训练。其他已上市产品可练通用沟通；适应症、用法和疗效仍需以当前获批说明书为准。</p>
  </div>;
}
