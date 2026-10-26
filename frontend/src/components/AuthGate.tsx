import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { clearAuthorization, encodeBasic, readAuthorization, saveAuthorization, verifyAuthorization } from "../auth";

type Status = "checking" | "login" | "ready";

export default function AuthGate({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<Status>("checking");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const saved = readAuthorization();
    if (!saved) { setStatus("login"); return; }
    verifyAuthorization(saved).then((valid) => {
      if (!active) return;
      if (valid) { saveAuthorization(saved); setStatus("ready"); }
      else { clearAuthorization(); setStatus("login"); }
    }).catch(() => {
      if (active) { setError("连接训练服务器失败，请稍后重试。"); setStatus("login"); }
    });
    return () => { active = false; };
  }, []);

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      const value = encodeBasic(username.trim(), password);
      if (!await verifyAuthorization(value)) {
        setError("账号或密码不正确，请重试。");
        return;
      }
      saveAuthorization(value);
      setPassword("");
      setStatus("ready");
    } catch {
      setError("连接训练服务器失败，请检查网络后重试。");
    } finally { setBusy(false); }
  }

  if (status === "ready") return <>{children}</>;
  return <div className="game-auth-screen">
    <div className="game-auth-panel">
      <div className="game-brand !border-0 !p-0">
        <div className="game-logo"><img src={`${import.meta.env.BASE_URL}innovent-logo.png`} alt="信达生物制药" /></div>
        <div><strong>医学沟通训练台</strong><small>FIELD SIMULATOR</small></div>
      </div>
      <p className="game-kicker mt-10">ACCESS CHECK / 进入训练</p>
      <h1 className="game-title mt-3">登录后开始任务</h1>
      <p className="game-muted mt-3 text-sm leading-6">输入演示账户即可进入；训练记录仅在当前浏览器保存入口。</p>
      {status === "checking" ? <p className="game-muted mt-8 text-sm">正在验证登录…</p> :
        <form className="mt-8 grid gap-4" onSubmit={(event) => void login(event)}>
          <label className="text-xs font-bold text-[#c7dce7]">账号
            <input className="game-field mt-2" name="username" autoComplete="username" required value={username} onChange={(event) => setUsername(event.target.value)} />
          </label>
          <label className="text-xs font-bold text-[#c7dce7]">密码
            <input className="game-field mt-2" name="password" type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} />
          </label>
          {error && <div className="game-alert" role="alert">{error}</div>}
          <button className="game-btn mt-2 w-full" type="submit" disabled={busy}>{busy ? "正在验证…" : "进入训练 →"}</button>
        </form>}
      <a className="game-link mt-7 inline-block" href={import.meta.env.BASE_URL}>← 返回训练首页</a>
      <p className="mt-8 border-t border-[#2d4e61] pt-5 text-[11px] leading-5 text-[#819eaf]">独立培训演示原型，非信达生物官方系统。模拟内容不可作为医学或合规依据。</p>
    </div>
  </div>;
}
