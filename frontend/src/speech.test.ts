import { afterEach, describe, expect, it, vi } from "vitest";
import { speakDoctorReply, speechOutputAvailable } from "./speech";

afterEach(() => vi.unstubAllGlobals());

describe("模拟医生语音播报", () => {
  it("在浏览器中朗读中文并可停止", () => {
    const cancel = vi.fn();
    const speak = vi.fn();
    vi.stubGlobal("navigator", { userAgent: "Desktop Chrome" });
    vi.stubGlobal("window", { speechSynthesis: { cancel, speak } });
    vi.stubGlobal("SpeechSynthesisUtterance", class {
      lang = "";
      rate = 0;
      constructor(public text: string) {}
    });
    expect(speechOutputAvailable()).toBe(true);
    const stop = speakDoctorReply("  您先说说顾虑。  ", vi.fn());
    expect(speak).toHaveBeenCalledOnce();
    expect(speak.mock.calls[0][0]).toMatchObject({ text: "您先说说顾虑。", lang: "zh-CN", rate: 1 });
    stop();
    expect(cancel).toHaveBeenCalledTimes(2);
  });

  it("在安卓包装器中只发送本地语音指令", () => {
    const addEventListener = vi.fn();
    const removeEventListener = vi.fn();
    const location = { href: "" };
    vi.stubGlobal("navigator", { userAgent: "RepTrainerAndroid/1.0" });
    vi.stubGlobal("window", { location, addEventListener, removeEventListener });
    const stop = speakDoctorReply("您好，先谈谈您的关注点。", vi.fn());
    expect(location.href).toContain("reptrainer://speak?text=");
    expect(decodeURIComponent(location.href.split("text=")[1])).toBe("您好，先谈谈您的关注点。");
    expect(addEventListener).toHaveBeenCalledWith("rep-trainer-speech-error", expect.any(Function));
    stop();
    expect(location.href).toBe("reptrainer://stop");
    expect(removeEventListener).toHaveBeenCalledOnce();
  });
});
