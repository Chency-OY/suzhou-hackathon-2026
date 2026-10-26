import { afterEach, describe, expect, it, vi } from "vitest";
import { authorizationHeader, clearAuthorization, encodeBasic, saveAuthorization, verifyAuthorization } from "./auth";

afterEach(() => { clearAuthorization(); vi.unstubAllGlobals(); });

describe("browser login for protected API", () => {
  it("sends the entered credentials only in the API Authorization header", async () => {
    const request = vi.fn(async () => ({ ok: true }));
    vi.stubGlobal("fetch", request);
    const token = encodeBasic("demo", "example-password");
    expect(await verifyAuthorization(token)).toBe(true);
    expect(request).toHaveBeenCalledWith("/api/health", {
      headers: { Authorization: token }, cache: "no-store",
    });
    saveAuthorization(token);
    expect(authorizationHeader()).toEqual({ Authorization: token });
    clearAuthorization();
    expect(authorizationHeader()).toEqual({});
  });

  it("rejects invalid credentials", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: false })));
    expect(await verifyAuthorization(encodeBasic("demo", "wrong"))).toBe(false);
  });
});
