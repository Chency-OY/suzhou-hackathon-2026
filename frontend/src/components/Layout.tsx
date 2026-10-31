import { useEffect, useState, type FormEvent } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { currentAccount, logoutAccount, upgradeGuestAccount, type Account } from "../auth";

export default function Layout() {
  const [account, setAccount] = useState<Account | null>(null);
  const [logoutError, setLogoutError] = useState("");
  const [upgradeOpen, setUpgradeOpen] = useState(false);
  const [upgradeName, setUpgradeName] = useState("");
  const [upgradePassword, setUpgradePassword] = useState("");
  const [upgradeConfirm, setUpgradeConfirm] = useState("");
  const [upgradeBusy, setUpgradeBusy] = useState(false);
  const [upgradeError, setUpgradeError] = useState("");
  useEffect(() => { void currentAccount().then(setAccount).catch(() => {}); }, []);

  async function upgrade(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (upgradeBusy) return;
    if (upgradePassword !== upgradeConfirm) { setUpgradeError("两次输入的密码不一致。"); return; }
    setUpgradeBusy(true);
    setUpgradeError("");
    try {
      setAccount(await upgradeGuestAccount(upgradeName.trim(), upgradePassword));
      setUpgradeOpen(false);
      setUpgradePassword("");
      setUpgradeConfirm("");
    } catch (cause) { setUpgradeError(cause instanceof Error ? cause.message : "保存失败，请重试。"); }
    finally { setUpgradeBusy(false); }
  }

  return (
    <div className="game-shell">
      <aside className="game-sidebar">
        <div className="game-brand">
          <div className="game-logo">
            <img src={`${import.meta.env.BASE_URL}innovent-logo.png`} alt="信达生物制药" />
          </div>
          <div><strong>医学沟通训练台</strong><small>FIELD SIMULATOR</small></div>
        </div>

        <div className="mt-7 hidden px-3 text-[10px] font-bold tracking-[.18em] text-[#7496aa] lg:block">TRAINING MENU</div>
        <nav className="game-nav mt-3" aria-label="训练导航">
          <NavLink to="/home" className={({ isActive }) => isActive ? "active" : ""}>
            <b aria-hidden="true">01</b><span>任务大厅</span>
          </NavLink>
          <NavLink to="/progress" className={({ isActive }) => isActive ? "active" : ""}>
            <b aria-hidden="true">02</b><span>练习档案</span>
          </NavLink>
          <NavLink to="/products" className={({ isActive }) => isActive ? "active" : ""}>
            <b aria-hidden="true">03</b><span>信达产品目录</span>
          </NavLink>
          {account && !account.is_guest && <><NavLink to="/diary" className={({ isActive }) => isActive ? "active" : ""}>
            <b aria-hidden="true">04</b><span>前线日记</span>
          </NavLink>
          <NavLink to="/radar" className={({ isActive }) => isActive ? "active" : ""}>
            <b aria-hidden="true">05</b><span>学术雷达</span>
          </NavLink>
          </>}
        </nav>

        <div className="mt-auto hidden border-t border-[#254154] px-3 pt-5 lg:block">
          <div className="flex items-center gap-2 text-xs font-semibold text-[#c7dce7]"><span className="h-2 w-2 rounded-full bg-[#72d9bd]" />AI 模拟对话运行中</div>
          <p className="mt-3 text-[11px] leading-5 text-[#819fb1]">训练数据均为合成情境。模拟医生的回复不能作为医学或合规依据。</p>
        </div>
      </aside>

      <div className="game-main">
        <header className="game-topbar">
          <span>医学沟通模拟训练 / COMMAND CENTER</span>
          <span className="flex items-center gap-3"><span className="hidden items-center gap-2 sm:flex"><span className="h-1.5 w-1.5 rounded-full bg-[#72d9bd]" />DEMO BUILD 01</span><span className="max-w-24 truncate text-[#c9e9f2]" title={account?.is_guest ? "免登录试用" : account?.username}>{account?.is_guest ? "试用访客" : account?.username}</span><button type="button" className="game-link" onClick={() => { void logoutAccount().then(() => window.location.assign(`${import.meta.env.BASE_URL}home?auth=login`)).catch(() => setLogoutError("退出失败，请重试")); }}>{account?.is_guest ? "退出试用" : "退出登录"}</button></span>
        </header>
        {logoutError && <div className="game-alert mx-5 mt-3" role="alert">{logoutError}</div>}
        <div className="game-notice">独立培训演示原型，非信达生物官方系统。请以获批资料和正式审核意见为准。</div>
        {account?.is_guest && <div className="game-guest-banner"><span>试用模式 · 24 小时有效 · 可练 2 个情境</span><button type="button" onClick={() => setUpgradeOpen(true)}>创建账号，保留本次演练 →</button></div>}
        <main className="game-content"><Outlet /></main>
      </div>
      {upgradeOpen && <div className="game-upgrade-backdrop"><div className="game-upgrade-panel" role="dialog" aria-modal="true" aria-labelledby="upgrade-title"><button className="game-upgrade-close" type="button" onClick={() => setUpgradeOpen(false)} aria-label="关闭">×</button><p className="game-kicker">SAVE YOUR PROGRESS</p><h2 id="upgrade-title">保留这次试用的演练</h2><p>设置账号和密码后，刚才的对话与复盘会保留在你的账号中。</p><form onSubmit={(event) => void upgrade(event)}><label>账号<input className="game-field" autoFocus minLength={3} maxLength={24} pattern="[A-Za-z0-9_]{3,24}" required value={upgradeName} onChange={(event) => setUpgradeName(event.target.value)} /></label><label>密码<input className="game-field" type="password" autoComplete="new-password" minLength={8} maxLength={128} required value={upgradePassword} onChange={(event) => setUpgradePassword(event.target.value)} /></label><label>确认密码<input className="game-field" type="password" autoComplete="new-password" minLength={8} maxLength={128} required value={upgradeConfirm} onChange={(event) => setUpgradeConfirm(event.target.value)} /></label>{upgradeError && <div className="game-alert" role="alert">{upgradeError}</div>}<button className="game-btn" type="submit" disabled={upgradeBusy}>{upgradeBusy ? "正在保存…" : "保存为正式账号 →"}</button></form></div></div>}
    </div>
  );
}
