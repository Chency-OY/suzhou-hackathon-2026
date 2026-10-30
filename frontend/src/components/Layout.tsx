import { NavLink, Outlet } from "react-router-dom";

const link = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3 py-1.5 text-sm ${isActive ? "bg-sky-100 text-sky-900" : "text-slate-600 hover:bg-sky-50"}`;

export default function Layout() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-sky-100 bg-white/85 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="text-base font-semibold">医药代表智能演练助手</div>
          <nav className="flex gap-2">
            <NavLink to="/" end className={link}>演练场景</NavLink>
            <NavLink to="/progress" className={link}>我的成长</NavLink>
            <NavLink to="/team" className={link}>团队看板</NavLink>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
