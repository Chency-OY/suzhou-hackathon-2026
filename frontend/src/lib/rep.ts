let memo: string | null = null;

function fresh(): string {
  return `rep_${Math.random().toString(36).slice(2, 10)}`;
}

export function getRepId(): string {
  if (memo) return memo;
  try {
    let v = localStorage.getItem("rep_id");
    if (!v) {
      v = fresh();
      localStorage.setItem("rep_id", v);
    }
    memo = v;
  } catch {
    memo = fresh();
  }
  return memo;
}

export function readHints(): boolean {
  try {
    return localStorage.getItem("show_hints") !== "0";
  } catch {
    return true;
  }
}

export function writeHints(v: boolean): void {
  try {
    localStorage.setItem("show_hints", v ? "1" : "0");
  } catch {
    /* ignore */
  }
}

const HISTORY_KEY = "rep_trainer_sessions";

export function readSessionIds(): string[] {
  try {
    const ids = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]") as unknown;
    return Array.isArray(ids) ? ids.filter((x): x is string => typeof x === "string" && /^sess_[a-f0-9]+$/.test(x)).slice(0, 50) : [];
  } catch {
    return [];
  }
}

export function rememberSession(id: string): void {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify([id, ...readSessionIds().filter((x) => x !== id)].slice(0, 50)));
  } catch {
    /* 浏览器禁用本地存储时，仍允许继续演练。 */
  }
}
