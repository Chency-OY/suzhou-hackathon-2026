import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAsync } from "../hooks";
import type { ProductPortfolioItem } from "../types";

type View = "marketed" | "pipeline";

function ProductCard({ item }: { item: ProductPortfolioItem }) {
  const marketed = item.stage === "marketed";
  const stage = item.stage === "nda_review" ? "上市申请审评中" : item.stage === "pivotal" ? "关键临床阶段" : "已上市";
  return <article className="rounded-2xl border border-[#d8e6ee] bg-white p-5 shadow-[0_12px_30px_#2944580d]">
    <div className="flex items-start justify-between gap-3"><div><h3 className="text-lg font-extrabold text-[#163d5a]">{item.name}</h3><p className="mt-1 text-xs leading-5 text-[#587083]">{item.generic_name}</p></div><span className={`shrink-0 rounded-full px-2.5 py-1 text-[10px] font-bold ${marketed ? "bg-[#e6f6ef] text-[#146a50]" : "bg-[#fff3dc] text-[#8b5b12]"}`}>{stage}</span></div>
    <div className="mt-4 flex flex-wrap gap-2"><span className="rounded-full bg-[#eaf4fa] px-2.5 py-1 text-[11px] font-semibold text-[#176b91]">{item.area}</span><span className="rounded-full bg-[#f2f5f8] px-2.5 py-1 text-[11px] text-[#426174]">{item.modality}</span></div>
    <p className="mt-4 text-xs leading-6 text-[#475f72]">{item.overview}</p>
    <details className="mt-4 border-t border-[#e4edf2] pt-3 text-xs"><summary className="cursor-pointer font-bold text-[#176b91]">展开完整产品介绍</summary>
      <dl className="mt-3 grid grid-cols-[72px_1fr] gap-x-3 gap-y-2 leading-6"><dt className="text-[#6d8494]">作用靶点</dt><dd>{item.target}</dd><dt className="text-[#6d8494]">药物形式</dt><dd>{item.modality}</dd><dt className="text-[#6d8494]">主要领域</dt><dd>{item.area}</dd><dt className="text-[#6d8494]">当前状态</dt><dd>{stage}</dd></dl>
      {item.key_points.length > 0 && <ul className="mt-3 list-inside list-disc space-y-1.5 leading-6">{item.key_points.map((point) => <li key={point}>{point}</li>)}</ul>}
      <p className="mt-3 leading-6 text-[#6d8494]">{marketed ? "这是公开资料概览，具体适应症、用法及风险以现行获批说明书为准。" : "研究方向尚非获批适应症，不代表上市时间或临床结论。"}</p>
      <p className="mt-2 text-[11px] text-[#6d8494]">核对日期 {item.checked_on} · <a className="underline underline-offset-2" href={item.overview_source_url} target="_blank" rel="noreferrer">核对公司报告 ↗</a>{item.detail_source_url && <> · <a className="underline underline-offset-2" href={item.detail_source_url} target="_blank" rel="noreferrer">核对说明书 ↗</a></>}</p>
    </details>
    <Link className="mt-4 inline-flex rounded-lg bg-[#176b91] px-3 py-2 text-xs font-bold text-white" to={`/products/${item.id}/test`}>测试我对{item.name}的了解 →</Link>
    {item.id === "xinermei" && <Link className="ml-3 mt-4 inline-flex text-xs font-bold text-[#176b91]" to="/home?program=xinermei">进入情境演练 →</Link>}
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
    <p className="game-muted mt-3 max-w-3xl text-sm leading-7">直接查看每款产品的作用靶点、药物类型、主要领域和当前状态，也可以选择一款进行语音问答测试。研发项目仍未获批，不能作为上市产品介绍。</p>
    <div className="mt-6 flex flex-wrap items-center gap-2" role="tablist" aria-label="产品阶段">
      <button role="tab" aria-selected={view === "marketed"} className={`rounded-full px-4 py-2 text-xs font-bold ${view === "marketed" ? "bg-[#176b91] text-white" : "bg-white text-[#446173]"}`} type="button" onClick={() => setView("marketed")}>已上市 · {marketedCount}</button>
      <button role="tab" aria-selected={view === "pipeline"} className={`rounded-full px-4 py-2 text-xs font-bold ${view === "pipeline" ? "bg-[#176b91] text-white" : "bg-white text-[#446173]"}`} type="button" onClick={() => setView("pipeline")}>上市前项目 · {pipelineCount}</button>
    </div>
    <label className="mt-5 block max-w-md text-xs font-bold text-[#446173]">搜索名称或研发编号<input className="game-field mt-2" type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="例如：信尔美、IBI343" /></label>
    {loading && <div className="game-panel mt-5 p-6 text-sm">正在读取产品目录…</div>}
    {error && <div className="game-alert mt-5" role="alert">产品目录加载失败：{error}</div>}
    {!loading && !error && shown.length === 0 && <div className="game-panel mt-5 p-6 text-sm">没有符合条件的产品。</div>}
    <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{shown.map((item) => <ProductCard key={item.id} item={item} />)}</div>
    <p className="game-muted mt-7 text-xs leading-6">产品测试只依据这里列出的已核对公开资料评价基础知识；完整临床沟通仍须按当前获批说明书和正式审核资料准备。</p>
  </div>;
}
