import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { SIGNAL_LABEL, SIGNAL_POLARITY } from "../labels";
import { SIGNALS, type PlaybookCardView, type Signal, type TeamInfo, type TeamInsights } from "../types";

const message = (error: unknown) => error instanceof Error ? error.message : String(error);

export default function TeamPage() {
  const [team, setTeam] = useState<TeamInfo | null>(null);
  const [insights, setInsights] = useState<TeamInsights | null>(null);
  const [cards, setCards] = useState<PlaybookCardView[]>([]);
  const [inviteCode, setInviteCode] = useState("");
  const [teamName, setTeamName] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    api.getTeam().then(async (found) => {
      const [result, foundCards] = await Promise.all([api.getTeamInsights(), api.listPlaybookCards()]);
      if (active) { setTeam(found); setInsights(result); setCards(foundCards); }
    }).catch((cause) => { if (active && message(cause) !== "尚未加入团队") setError(message(cause)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const result = await api.createTeam(teamName.trim());
      setTeam(result); setInviteCode(result.invite_code); setInsights(await api.getTeamInsights()); setCards([]);
    } catch (cause) { setError(message(cause)); } finally { setBusy(false); }
  }

  async function join(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const result = await api.joinTeam(joinCode.trim());
      setTeam(result); setJoinCode(""); setInsights(await api.getTeamInsights()); setCards(await api.listPlaybookCards());
    } catch (cause) { setError(message(cause)); } finally { setBusy(false); }
  }

  async function leave() {
    setBusy(true); setError("");
    try { await api.leaveTeam(); setTeam(null); setInsights(null); setInviteCode(""); setCards([]); }
    catch (cause) { setError(message(cause)); } finally { setBusy(false); }
  }

  async function rotateInvite() {
    setBusy(true); setError("");
    try { const result = await api.rotateTeamInvite(); setTeam(result); setInviteCode(result.invite_code); }
    catch (cause) { setError(message(cause)); } finally { setBusy(false); }
  }

  async function approveCard(cardId: string) {
    setBusy(true); setError("");
    try { await api.approvePlaybookCard(cardId); setCards(await api.listPlaybookCards()); }
    catch (cause) { setError(message(cause)); } finally { setBusy(false); }
  }

  async function rejectCard(cardId: string) {
    setBusy(true); setError("");
    try { await api.rejectPlaybookCard(cardId); setCards(await api.listPlaybookCards()); }
    catch (cause) { setError(message(cause)); } finally { setBusy(false); }
  }

  const signals = (polarity: "good" | "bad") => SIGNALS.filter((signal) => SIGNAL_POLARITY[signal] === polarity && (insights?.signal_counts[signal] || 0) > 0)
    .sort((left, right) => (insights?.signal_counts[right] || 0) - (insights?.signal_counts[left] || 0));
  const signalList = (items: Signal[]) => items.length > 0 ? <ul className="mt-4 space-y-2">{items.map((signal) => <li key={signal} className="flex justify-between border-b border-[#dce8ee] pb-2 text-sm"><span>{SIGNAL_LABEL[signal]}</span><strong>{insights?.signal_counts[signal]} 次</strong></li>)}</ul>
    : <p className="game-muted mt-4 text-sm">目前没有可汇总的记录。</p>;

  return <div className="mx-auto max-w-5xl">
    <p className="game-kicker">TEAM LEARNING / 团队学习</p>
    <h1 className="game-title mt-2">把演练中的经验带给团队</h1>
    <p className="game-muted mt-3 max-w-3xl text-sm leading-7">加入同一团队后，这里汇总完成演练的沟通信号与训练参考分。只显示次数和均分，不展示队友的日记、学术雷达、账号或对话原文；退出后你的历史练习不再计入团队汇总。</p>
    {loading && <div className="game-panel mt-6 p-6 text-sm">正在读取团队…</div>}
    {error && <div className="game-alert mt-5" role="alert">{error}</div>}
    {!loading && !team && <div className="mt-6 grid gap-4 md:grid-cols-2">
      <form className="game-panel p-5" onSubmit={(event) => void create(event)}><h2 className="text-base font-bold">创建团队</h2><p className="game-muted mt-2 text-xs">创建后可分享一次性显示的邀请码。</p><label className="mt-5 block text-xs font-bold">团队名称<input className="game-field mt-2" value={teamName} minLength={2} maxLength={60} required onChange={(event) => setTeamName(event.target.value)} placeholder="例如：内分泌训练组" /></label><button className="game-btn mt-4" type="submit" disabled={busy}>创建团队</button></form>
      <form className="game-panel p-5" onSubmit={(event) => void join(event)}><h2 className="text-base font-bold">加入团队</h2><p className="game-muted mt-2 text-xs">向团队创建者获取邀请码后加入。</p><label className="mt-5 block text-xs font-bold">邀请码<input className="game-field mt-2" value={joinCode} minLength={12} maxLength={64} required onChange={(event) => setJoinCode(event.target.value)} placeholder="输入邀请码" /></label><button className="game-btn mt-4" type="submit" disabled={busy}>加入团队</button></form>
    </div>}
    {team && <>
      <section className="game-panel mt-6 p-5 sm:p-7"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-lg font-bold">{team.name}</h2><p className="game-muted mt-1 text-xs">{team.member_count} 位成员 · {team.role === "owner" ? "创建者" : "成员"}</p></div>{team.role === "member" ? <button className="game-btn game-btn-outline" type="button" disabled={busy} onClick={() => void leave()}>退出团队</button> : <button className="game-btn game-btn-outline" type="button" disabled={busy} onClick={() => void rotateInvite()}>生成新邀请码</button>}</div>
        {inviteCode && <div className="game-alert mt-5"><p className="text-xs">请现在保存邀请码，关闭页面后不会再次显示。</p><code className="mt-2 block break-all text-sm font-bold">{inviteCode}</code></div>}
      </section>
      <div className="mt-4 grid gap-4 sm:grid-cols-3"><div className="game-panel p-5"><p className="game-muted text-xs">已完成演练</p><strong className="mt-2 block text-2xl">{insights?.completed_sessions ?? 0}</strong></div><div className="game-panel p-5"><p className="game-muted text-xs">已评分演练</p><strong className="mt-2 block text-2xl">{insights?.scored_sessions ?? 0}</strong></div><div className="game-panel p-5"><p className="game-muted text-xs">训练参考均分</p><strong className="mt-2 block text-2xl">{insights?.average_score ?? "暂无"}</strong></div></div>
      <div className="mt-4 grid gap-4 md:grid-cols-2"><section className="game-panel p-5"><h2 className="text-base font-bold">团队常见失误</h2><p className="game-muted mt-1 text-xs">按出现该信号的演练次数计算。</p>{signalList(signals("bad"))}</section><section className="game-panel p-5"><h2 className="text-base font-bold">团队有效动作</h2><p className="game-muted mt-1 text-xs">这些是沟通信号，并不代表医学内容已核实。</p>{signalList(signals("good"))}</section></div>
      <section className="game-panel mt-4 p-5 sm:p-7"><h2 className="text-base font-bold">团队打法卡片</h2><p className="game-muted mt-2 text-xs leading-6">成员可从自己的高分复盘推荐候选卡片。创建者审核后，卡片会生成一个只供本团队练习的新情境；卡片只讨论沟通方法，不能作为医学结论。</p>{cards.length === 0 ? <p className="game-muted mt-5 text-sm">暂无卡片。完成高分演练后，可在复盘页推荐沟通方法。</p> : <div className="mt-5 space-y-3">{cards.map((card) => <article className="rounded-lg border border-[#d5e4ed] bg-[#f7fafc] p-4" key={card.id}><div className="flex flex-wrap justify-between gap-2"><h3 className="text-sm font-bold">{card.title}</h3><span className="text-xs text-[#176b91]">{card.status === "approved" ? "已加入团队打法库" : card.status === "rejected" ? "未通过审核" : "待审核"}</span></div><p className="game-muted mt-2 text-xs leading-6">情境：{card.situation}</p><p className="mt-2 text-sm leading-6">做法：{card.effective_response_pattern}</p>{card.example_lines.length > 0 && <p className="game-muted mt-2 text-xs leading-6">示例：{card.example_lines.join(" / ")}</p>}<div className="mt-3">{card.status === "approved" && card.scenario_id ? <Link className="game-link text-xs" to={`/scenarios/${card.scenario_id}`}>练习这个情境 →</Link> : card.status === "rejected" ? <span className="game-muted text-xs">这张卡片不会进入团队训练</span> : team.role === "owner" ? <div className="flex flex-wrap gap-2"><button className="game-btn" type="button" disabled={busy} onClick={() => void approveCard(card.id)}>审核通过并生成练习</button><button className="game-btn game-btn-outline" type="button" disabled={busy} onClick={() => void rejectCard(card.id)}>不采用</button></div> : <span className="game-muted text-xs">等待团队创建者审核</span>}</div></article>)}</div>}</section>
      <Link className="game-btn mt-6" to="/home">针对常见问题继续演练 →</Link>
    </>}
  </div>;
}
