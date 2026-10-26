import { afterEach, describe, expect, it, vi } from "vitest";
import { currentAccount, loginAccount, logoutAccount, registerAccount } from "./auth";

afterEach(() => { vi.unstubAllGlobals(); });

describe("individual account API", () => {
  it("registers with a same-origin cookie and reads that account", async () => {
    const account = { id: "usr_1", username: "pilot" };
    const request = vi.fn(async () => ({ ok: true, json: async () => account }));
    vi.stubGlobal("fetch", request);
    expect(await registerAccount("pilot", "example-password")).toEqual(account);
    expect(request).toHaveBeenCalledWith("/api/auth/register", {
      method: "POST", credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: "pilot", password: "example-password" }),
    });
    expect(await currentAccount()).toEqual(account);
    expect(request).toHaveBeenCalledWith("/api/auth/me", { credentials: "same-origin", cache: "no-store" });
    await logoutAccount();
    expect(request).toHaveBeenCalledWith("/api/auth/logout", { method: "POST", credentials: "same-origin" });
  });

  it("shows invalid login and treats 401 from me as signed out", async () => {
    vi.stubGlobal("fetch", vi.fn(async (url: string) => url.endsWith("/me")
      ? { status: 401 }
      : { ok: false, status: 401, json: async () => ({ detail: { error: { message: "账号或密码不正确" } } }) }));
    expect(await currentAccount()).toBeNull();
    await expect(loginAccount("pilot", "wrong-password")).rejects.toThrow("账号或密码不正确");
  });
});
