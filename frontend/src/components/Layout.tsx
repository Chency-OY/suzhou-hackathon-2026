import { NavLink, Outlet } from "react-router-dom";

const link = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3 py-1.5 text-sm ${isActive ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-200"}`;

export default function Layout() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="flex items-center gap-3">
            <img className="h-8 w-auto max-w-[110px] object-contain sm:h-9 sm:max-w-none" src={`${import.meta.env.BASE_URL}innovent-logo.png`} alt="信达生物制药" />
            <span className="border-l border-slate-200 pl-3 text-sm font-semibold text-slate-800">医学沟通训练台</span>
          </div>
          <nav className="flex gap-2">
            <NavLink to="/home" className={link}>选择情境</NavLink>
            <NavLink to="/progress" className={link}>练习记录</NavLink>
          </nav>
        </div>
      </header>
      <div className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-center text-xs text-amber-900">
        非信达生物官方系统 · 离线演示模式：医生回复由规则模拟；医学与合规判断请核对经批准的正式资料。
      </div>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
