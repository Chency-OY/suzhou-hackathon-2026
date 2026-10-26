export interface Account { id: string; username: string }

const url = (path: string) => `${import.meta.env.BASE_URL}api/auth/${path}`;

async function readError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return body?.detail?.error?.message ?? body?.detail?.[0]?.msg ?? `请求失败（${response.status}）`;
  } catch { return `请求失败（${response.status}）`; }
}

export async function currentAccount(): Promise<Account | null> {
  const response = await fetch(url("me"), { credentials: "same-origin", cache: "no-store" });
  if (response.status === 401) return null;
  if (!response.ok) throw new Error(await readError(response));
  return response.json() as Promise<Account>;
}

async function submit(path: "login" | "register", username: string, password: string): Promise<Account> {
  const response = await fetch(url(path), {
    method: "POST", credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) throw new Error(await readError(response));
  return response.json() as Promise<Account>;
}

export const loginAccount = (username: string, password: string) => submit("login", username, password);
export const registerAccount = (username: string, password: string) => submit("register", username, password);

export async function logoutAccount(): Promise<void> {
  const response = await fetch(url("logout"), { method: "POST", credentials: "same-origin" });
  if (!response.ok) throw new Error(await readError(response));
}
