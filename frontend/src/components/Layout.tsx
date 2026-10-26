import { NavLink, Outlet } from "react-router-dom";

export default function Layout() {
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
        </nav>

        <div className="mt-auto hidden border-t border-[#254154] px-3 pt-5 lg:block">
          <div className="flex items-center gap-2 text-xs font-semibold text-[#c7dce7]"><span className="h-2 w-2 rounded-full bg-[#72d9bd]" />离线演示运行中</div>
          <p className="mt-3 text-[11px] leading-5 text-[#819fb1]">训练数据均为合成情境。模拟医生的回复不能作为医学或合规依据。</p>
        </div>
      </aside>

      <div className="game-main">
        <header className="game-topbar">
          <span>医学沟通模拟训练 / COMMAND CENTER</span>
          <span className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-[#72d9bd]" />DEMO BUILD 01</span>
        </header>
        <div className="game-notice">独立培训演示原型，非信达生物官方系统。请以获批资料和正式审核意见为准。</div>
        <main className="game-content"><Outlet /></main>
      </div>
    </div>
  );
}
