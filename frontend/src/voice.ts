type VoiceResult = { text?: string; error?: string; ended?: boolean; id?: string };

interface BrowserSpeechRecognition {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
}

type SpeechWindow = Window & {
  SpeechRecognition?: new () => BrowserSpeechRecognition;
  webkitSpeechRecognition?: new () => BrowserSpeechRecognition;
};

export function voiceInputAvailable(): boolean {
  const browser = window as SpeechWindow;
  return navigator.userAgent.includes("RepTrainerAndroid") ||
    !!(browser.SpeechRecognition || browser.webkitSpeechRecognition);
}

export function startVoiceInput(
  onText: (text: string) => void,
  onError: (message: string) => void,
  onListening: (active: boolean) => void,
): () => void {
  if (navigator.userAgent.includes("RepTrainerAndroid")) {
    let active = true;
    let stopping = false;
    let stopTimer: ReturnType<typeof setTimeout> | null = null;
    const id = `${Date.now().toString(36)}${Math.random().toString(36).slice(2)}`;
    const receive = (event: Event) => {
      const detail = (event as CustomEvent<VoiceResult>).detail;
      if (detail?.id !== id) return;
      if (detail?.text?.trim()) onText(detail.text.trim());
      if (detail?.error) onError(detail.error);
      if (detail?.ended) {
        active = false;
        stopping = false;
        if (stopTimer) clearTimeout(stopTimer);
        onListening(false);
        window.removeEventListener("rep-trainer-voice-result", receive);
      }
    };
    window.addEventListener("rep-trainer-voice-result", receive);
    onListening(true);
    window.location.href = `reptrainer://voice?id=${encodeURIComponent(id)}`;
    return () => {
      if (!active || stopping) return;
      stopping = true;
      window.location.href = `reptrainer://voice-stop?id=${encodeURIComponent(id)}`;
      stopTimer = setTimeout(() => {
        active = false;
        onListening(false);
        window.removeEventListener("rep-trainer-voice-result", receive);
      }, 3000);
    };
  }

  const browser = window as SpeechWindow;
  const Recognition = browser.SpeechRecognition || browser.webkitSpeechRecognition;
  if (!Recognition) {
    onError("当前浏览器不支持语音输入，请使用安卓 App 或键盘输入。");
    return () => {};
  }
  const recognition = new Recognition();
  recognition.lang = "zh-CN";
  recognition.interimResults = false;
  recognition.continuous = true;
  let active = true;
  let delivered = 0;
  let consecutiveErrors = 0;
  let restartTimer: ReturnType<typeof setTimeout> | null = null;
  let stopTimer: ReturnType<typeof setTimeout> | null = null;
  const finish = (reason?: string) => {
    if (!active) return;
    active = false;
    if (restartTimer) clearTimeout(restartTimer);
    if (stopTimer) clearTimeout(stopTimer);
    if (reason) onError(reason);
    onListening(false);
  };
  recognition.onresult = (event) => {
    // Results are cumulative until this recognition run ends.
    for (let i = delivered; i < event.results.length; i += 1) {
      const text = event.results[i]?.[0]?.transcript?.trim();
      if (text) onText(text);
      if (text) consecutiveErrors = 0;
    }
    delivered = event.results.length;
  };
  recognition.onerror = (event) => {
    if (["not-allowed", "service-not-allowed", "audio-capture"].includes(event.error)) {
      finish("麦克风权限或语音服务不可用，请检查手机设置。");
    } else if (event.error !== "no-speech" && event.error !== "aborted" && ++consecutiveErrors >= 3) {
      finish("语音服务连续中断，请检查网络或改用键盘输入。");
    }
    // Silence ends one segment; onend resumes while the user still wants to record.
  };
  recognition.onend = () => {
    if (!active) {
      if (stopTimer) clearTimeout(stopTimer);
      onListening(false);
      return;
    }
    delivered = 0;
    restartTimer = setTimeout(() => {
      if (!active) return;
      try { recognition.start(); }
      catch { finish("语音识别无法继续，请重新点麦克风。"); }
    }, 250);
  };
  try {
    recognition.start();
    onListening(true);
  } catch {
    finish("无法启动语音识别，请检查麦克风权限。");
  }
  return () => {
    if (!active) return;
    active = false;
    if (restartTimer) clearTimeout(restartTimer);
    recognition.stop();
    stopTimer = setTimeout(() => onListening(false), 3000);
  };
}
