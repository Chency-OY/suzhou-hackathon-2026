type VoiceResult = { text?: string; error?: string };

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
    const receive = (event: Event) => {
      const detail = (event as CustomEvent<VoiceResult>).detail;
      onListening(false);
      if (detail?.text?.trim()) onText(detail.text.trim());
      else if (detail?.error) onError(detail.error);
    };
    window.addEventListener("rep-trainer-voice-result", receive);
    onListening(true);
    window.location.href = "reptrainer://voice";
    return () => window.removeEventListener("rep-trainer-voice-result", receive);
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
  recognition.continuous = false;
  recognition.onresult = (event) => {
    const text = event.results[0]?.[0]?.transcript?.trim();
    if (text) onText(text);
  };
  recognition.onerror = (event) => onError(`语音识别未完成：${event.error}`);
  recognition.onend = () => onListening(false);
  try {
    recognition.start();
    onListening(true);
  } catch {
    onListening(false);
    onError("无法启动语音识别，请检查麦克风权限。");
  }
  return () => recognition.stop();
}
