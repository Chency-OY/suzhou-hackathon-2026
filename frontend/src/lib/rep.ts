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
