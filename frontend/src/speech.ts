type SpeechError = { error?: string };

export function speechOutputAvailable(): boolean {
  return navigator.userAgent.includes("RepTrainerAndroid") || "speechSynthesis" in window;
}

export function stopSpeechOutput(): void {
  if (navigator.userAgent.includes("RepTrainerAndroid")) {
    window.location.href = "reptrainer://stop";
  } else if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}

export function speakDoctorReply(text: string, onError: (message: string) => void): () => void {
  const spoken = text.trim().slice(0, 500);
  if (!spoken || !speechOutputAvailable()) return () => {};
  stopSpeechOutput();
  if (navigator.userAgent.includes("RepTrainerAndroid")) {
    const error = (event: Event) => {
      const detail = (event as CustomEvent<SpeechError>).detail;
      if (detail?.error) onError(detail.error);
    };
    window.addEventListener("rep-trainer-speech-error", error);
    window.location.href = `reptrainer://speak?text=${encodeURIComponent(spoken)}`;
    return () => { window.removeEventListener("rep-trainer-speech-error", error); stopSpeechOutput(); };
  }
  const utterance = new SpeechSynthesisUtterance(spoken);
  utterance.lang = "zh-CN";
  utterance.rate = 1;
  utterance.onerror = () => onError("语音播报暂不可用，可以继续看文字对话。");
  window.speechSynthesis.speak(utterance);
  return () => window.speechSynthesis.cancel();
}
