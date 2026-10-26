import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { currentAccount, loginAccount, registerAccount, type Account } from "../auth";

type Status = "checking" | "login" | "register" | "ready";

export default function AuthGate({ children }: { children: ReactNode }) {
  const initialMode = new URLSearchParams(window.location.search).get("auth") === "register" ? "register" : "login";
  const [status, setStatus] = useState<Status>("checking");
  const [account, setAccount] = useState<Account | null>(null);
  const [mode, setMode] = useState<"login" | "register">(initialMode);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    currentAccount().then((found) => {
      if (!active) return;
      setAccount(found);
      setStatus(found ? "ready" : mode);
    }).catch(() => {
      if (active) { setError("连接训练服务器失败，请稍后重试。"); setStatus(mode); }
    });
    return () => { active = false; };
    // Only check once when the training page opens.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function changeMode(next: "login" | "register") {
    setMode(next);
    setStatus(next);
    setError("");
    setPassword("");
    setConfirm("");
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    if (mode === "register" && password !== confirm) {
      setError("两次输入的密码不一致。");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const found = mode === "register"
        ? await registerAccount(username.trim(), password)
        : await loginAccount(username.trim(), password);
      setAccount(found);
      setPassword("");
      setConfirm("");
      setStatus("ready");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "请求失败，请稍后再试。");
    } finally { setBusy(false); }
  }

  if (status === "ready" && account) return <>{children}</>;
  return <div className="game-auth-screen">
    <div className="game-auth-panel">
      <div className="game-brand !border-0 !p-0">
        <div className="game-logo"><img src={`${import.meta.env.BASE_URL}innovent-logo.png`} alt="信达生物制药" /></div>
        <div><strong>医学沟通训练台</strong><small>FIELD SIMULATOR</small></div>
      </div>
      <p className="game-kicker mt-10">ACCESS CHECK / 进入训练</p>
      <h1 className="game-title mt-3">{mode === "register" ? "创建你的训练账号" : "欢迎回来"}</h1>
      <p className="game-muted mt-3 text-sm leading-6">{mode === "register" ? "注册后，练习记录只属于你的账号。" : "登录后继续训练，查看你的练习记录。"}</p>
      <div className="mt-7 grid grid-cols-2 gap-2" role="group" aria-label="账号入口">
        <button type="button" aria-pressed={mode === "login"} className={`game-auth-tab ${mode === "login" ? "active" : ""}`} onClick={() => changeMode("login")}>登录</button>
        <button type="button" aria-pressed={mode === "register"} className={`game-auth-tab ${mode === "register" ? "active" : ""}`} onClick={() => changeMode("register")}>注册</button>
      </div>
      {status === "checking" ? <p className="game-muted mt-8 text-sm">正在检查登录状态…</p> :
        <form className="mt-6 grid gap-4" onSubmit={(event) => void submit(event)}>
          <label className="text-xs font-bold text-[#c7dce7]">账号
            <input className="game-field mt-2" name="username" autoComplete="username" minLength={3} maxLength={24} pattern="[A-Za-z0-9_]{3,24}" required value={username} onChange={(event) => setUsername(event.target.value)} placeholder="3–24 位字母、数字或下划线" />
          </label>
          <label className="text-xs font-bold text-[#c7dce7]">密码
            <input className="game-field mt-2" name="password" type="password" autoComplete={mode === "register" ? "new-password" : "current-password"} minLength={8} maxLength={128} required value={password} onChange={(event) => setPassword(event.target.value)} placeholder={mode === "register" ? "至少 8 位" : "输入密码"} />
          </label>
          {mode === "register" && <label className="text-xs font-bold text-[#c7dce7]">确认密码
            <input className="game-field mt-2" name="confirm" type="password" autoComplete="new-password" minLength={8} required value={confirm} onChange={(event) => setConfirm(event.target.value)} />
          </label>}
          {error && <div className="game-alert" role="alert">{error}</div>}
          <button className="game-btn mt-2 w-full" type="submit" disabled={busy}>{busy ? "正在处理…" : mode === "register" ? "创建账号 →" : "登录 →"}</button>
        </form>}
      <a className="game-link mt-7 inline-block" href={import.meta.env.BASE_URL}>← 返回训练首页</a>
      <p className="mt-8 border-t border-[#2d4e61] pt-5 text-[11px] leading-5 text-[#819eaf]">独立培训演示原型，非信达生物官方系统。请勿使用真实患者信息；模拟内容不可作为医学或合规依据。</p>
    </div>
  </div>;
}
