const STORAGE_KEY = "rep_trainer_demo_auth";

export function encodeBasic(username: string, password: string): string {
  const bytes = new TextEncoder().encode(`${username}:${password}`);
  let raw = "";
  for (const byte of bytes) raw += String.fromCharCode(byte);
  return `Basic ${btoa(raw)}`;
}

export function readAuthorization(): string | null {
  try { return sessionStorage.getItem(STORAGE_KEY); }
  catch { return null; }
}

export function saveAuthorization(value: string): void {
  try { sessionStorage.setItem(STORAGE_KEY, value); }
  catch { /* Browsers with disabled storage can still use the current tab until refresh. */ }
  currentAuthorization = value;
}

let currentAuthorization: string | null = null;

export function authorizationHeader(): Record<string, string> {
  const value = currentAuthorization ?? readAuthorization();
  return value ? { Authorization: value } : {};
}

export function clearAuthorization(): void {
  currentAuthorization = null;
  try { sessionStorage.removeItem(STORAGE_KEY); }
  catch { /* ignore */ }
}

export async function verifyAuthorization(value: string): Promise<boolean> {
  const response = await fetch(`${import.meta.env.BASE_URL}api/health`, {
    headers: { Authorization: value },
    cache: "no-store",
  });
  return response.ok;
}
