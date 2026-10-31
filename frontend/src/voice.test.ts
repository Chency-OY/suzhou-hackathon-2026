import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { startVoiceInput } from "./voice";

class FakeRecognition {
  lang = "";
  interimResults = false;
  continuous = false;
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null = null;
  onerror: ((event: { error: string }) => void) | null = null;
  onend: (() => void) | null = null;
  start = vi.fn();
  stop = vi.fn();
}

describe("持续语音输入", () => {
  beforeEach(() => { vi.useFakeTimers(); });
  afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); });

  it("累积多段结果，静音后续听，直到用户点停止", () => {
    const instance = new FakeRecognition();
    vi.stubGlobal("window", { SpeechRecognition: class { constructor() { return instance; } } });
    vi.stubGlobal("navigator", { userAgent: "Browser" });
    const text = vi.fn();
    const listening = vi.fn();
    const stop = startVoiceInput(text, vi.fn(), listening);
    expect(instance.continuous).toBe(true);
    expect(instance.start).toHaveBeenCalledTimes(1);
    instance.onresult?.({ results: [[{ transcript: "第一句" }]] });
    instance.onresult?.({ results: [[{ transcript: "第一句" }], [{ transcript: "第二句" }]] });
    expect(text.mock.calls.map((call) => call[0])).toEqual(["第一句", "第二句"]);
    instance.onerror?.({ error: "no-speech" });
    instance.onend?.();
    expect(listening).not.toHaveBeenCalledWith(false);
    vi.advanceTimersByTime(250);
    expect(instance.start).toHaveBeenCalledTimes(2);
    instance.onresult?.({ results: [[{ transcript: "第三句" }]] });
    expect(text.mock.calls.map((call) => call[0])).toEqual(["第一句", "第二句", "第三句"]);
    stop();
    instance.onend?.();
    vi.advanceTimersByTime(1000);
    expect(instance.start).toHaveBeenCalledTimes(2);
    expect(instance.stop).toHaveBeenCalledTimes(1);
    expect(listening).toHaveBeenLastCalledWith(false);
  });

  it("权限被拒后退出收音且不重启", () => {
    const instance = new FakeRecognition();
    vi.stubGlobal("window", { webkitSpeechRecognition: class { constructor() { return instance; } } });
    vi.stubGlobal("navigator", { userAgent: "Browser" });
    const error = vi.fn();
    const listening = vi.fn();
    startVoiceInput(vi.fn(), error, listening);
    instance.onerror?.({ error: "not-allowed" });
    instance.onend?.();
    vi.advanceTimersByTime(1000);
    expect(instance.start).toHaveBeenCalledTimes(1);
    expect(error).toHaveBeenCalledTimes(1);
    expect(listening).toHaveBeenLastCalledWith(false);
  });

  it("安卓包装器点停止后仍接收最后一段，再结束", () => {
    const browser = new EventTarget() as EventTarget & { location: { href: string } };
    browser.location = { href: "" };
    vi.stubGlobal("window", browser);
    vi.stubGlobal("navigator", { userAgent: "RepTrainerAndroid/1.0" });
    const text = vi.fn();
    const listening = vi.fn();
    const stop = startVoiceInput(text, vi.fn(), listening);
    const id = new URL(browser.location.href).searchParams.get("id");
    expect(id).toBeTruthy();
    stop();
    expect(browser.location.href).toContain("voice-stop");
    expect(listening).not.toHaveBeenCalledWith(false);
    const event = new Event("rep-trainer-voice-result") as Event & { detail: unknown };
    event.detail = { id, text: "停止前最后一段", ended: true };
    browser.dispatchEvent(event);
    expect(text).toHaveBeenCalledWith("停止前最后一段");
    expect(listening).toHaveBeenLastCalledWith(false);
  });
});
