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
