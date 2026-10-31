package online.chenxiouyang.reptrainer;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.Manifest;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.webkit.CookieManager;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import org.json.JSONObject;

import java.util.ArrayList;
import java.util.Locale;

public class MainActivity extends Activity {
    private static final int MICROPHONE_REQUEST = 1001;
    private static final String HOME = "https://chenxi-ouyang.online/rep-trainer/diary";
    private WebView webView;
    private TextToSpeech speech;
    private boolean speechReady = false;
    private SpeechRecognizer recognizer;
    private final Handler voiceHandler = new Handler(Looper.getMainLooper());
    private boolean voiceActive = false;
    private boolean voiceStopping = false;
    private String voiceId = "";
    private int consecutiveVoiceErrors = 0;
    private int voiceGeneration = 0;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        webView = new WebView(this);
        setContentView(webView);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setUserAgentString(settings.getUserAgentString() + " RepTrainerAndroid/1.0");
        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, false);
        speech = new TextToSpeech(this, new TextToSpeech.OnInitListener() {
            @Override
            public void onInit(final int status) {
                webView.post(new Runnable() {
                    @Override
                    public void run() {
                        if (status == TextToSpeech.SUCCESS && speech != null) {
                            int language = speech.setLanguage(Locale.SIMPLIFIED_CHINESE);
                            speechReady = language != TextToSpeech.LANG_MISSING_DATA
                                    && language != TextToSpeech.LANG_NOT_SUPPORTED;
                        }
                    }
                });
            }
        });
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return handleUrl(url);
            }

        });
        if (state == null) webView.loadUrl(HOME);
        else webView.restoreState(state);
    }

    private boolean handleUrl(String url) {
        Uri uri = Uri.parse(url);
        if ("reptrainer".equals(uri.getScheme()) && "voice".equals(uri.getHost())) {
            startVoiceInput(uri.getQueryParameter("id"));
            return true;
        }
        if ("reptrainer".equals(uri.getScheme()) && "voice-stop".equals(uri.getHost())) {
            if (voiceId.equals(uri.getQueryParameter("id"))) stopVoiceInput();
            return true;
        }
        if ("reptrainer".equals(uri.getScheme()) && "speak".equals(uri.getHost())) {
            String text = uri.getQueryParameter("text");
            if (text == null || text.length() > 500 || !speechReady) {
                sendSpeechError("语音播报暂不可用，可以继续看文字对话。");
            } else if (speech.speak(text, TextToSpeech.QUEUE_FLUSH, null, "doctor_reply") == TextToSpeech.ERROR) {
                sendSpeechError("语音播报失败，可以继续看文字对话。");
            }
            return true;
        }
        if ("reptrainer".equals(uri.getScheme()) && "stop".equals(uri.getHost())) {
            if (speech != null) speech.stop();
            return true;
        }
        if ("reptrainer".equals(uri.getScheme())) return true;
        if ("https".equals(uri.getScheme()) && "chenxi-ouyang.online".equals(uri.getHost())
                && uri.getPath() != null && uri.getPath().startsWith("/rep-trainer/")) return false;
        try { startActivity(new Intent(Intent.ACTION_VIEW, uri)); }
        catch (ActivityNotFoundException ignored) { }
        return true;
    }

    private void startVoiceInput(String id) {
        if (id == null || id.isEmpty()) return;
        if (voiceActive) endVoiceInput("");
        voiceGeneration++;
        voiceId = id;
        voiceActive = true;
        voiceStopping = false;
        consecutiveVoiceErrors = 0;
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, MICROPHONE_REQUEST);
            return;
        }
        beginVoiceSegment();
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grants) {
        super.onRequestPermissionsResult(requestCode, permissions, grants);
        if (requestCode != MICROPHONE_REQUEST || !voiceActive) return;
        if (grants.length > 0 && grants[0] == PackageManager.PERMISSION_GRANTED) beginVoiceSegment();
        else endVoiceInput("麦克风权限未开启，请在手机设置中允许录音。");
    }

    private void beginVoiceSegment() {
        if (!voiceActive || voiceStopping) return;
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            endVoiceInput("手机未安装可用的语音识别服务，请用键盘输入。");
            return;
        }
        if (recognizer == null) {
            final int generation = voiceGeneration;
            recognizer = SpeechRecognizer.createSpeechRecognizer(this);
            recognizer.setRecognitionListener(new RecognitionListener() {
                @Override public void onReadyForSpeech(Bundle params) { }
                @Override public void onBeginningOfSpeech() { }
                @Override public void onRmsChanged(float rmsdB) { }
                @Override public void onBufferReceived(byte[] buffer) { }
                @Override public void onEndOfSpeech() { }
                @Override public void onEvent(int eventType, Bundle params) { }
                @Override public void onPartialResults(Bundle partialResults) { }
                @Override public void onResults(Bundle results) {
                    if (generation != voiceGeneration || !voiceActive) return;
                    ArrayList<String> words = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                    if (words != null && !words.isEmpty()) sendVoiceResult(words.get(0), "", false);
                    consecutiveVoiceErrors = 0;
                    if (voiceStopping) endVoiceInput("");
                    else scheduleNextSegment(250);
                }
                @Override public void onError(int error) {
                    if (generation != voiceGeneration || !voiceActive) return;
                    if (voiceStopping) { endVoiceInput(""); return; }
                    if (error == SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS) {
                        endVoiceInput("麦克风权限未开启，请在手机设置中允许录音。");
                        return;
                    }
                    if (error == SpeechRecognizer.ERROR_NO_MATCH || error == SpeechRecognizer.ERROR_SPEECH_TIMEOUT) {
                        scheduleNextSegment(250);
                        return;
                    }
                    if (++consecutiveVoiceErrors >= 3) {
                        endVoiceInput("语音服务连续中断，请检查网络或改用键盘输入。");
                        return;
                    }
                    scheduleNextSegment(700);
                }
            });
        }
        Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "zh-CN");
        intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1);
        try { recognizer.startListening(intent); }
        catch (RuntimeException ignored) { endVoiceInput("无法启动语音识别，请检查麦克风权限。"); }
    }

    private void scheduleNextSegment(long delay) {
        if (!voiceActive || voiceStopping) return;
        final int generation = voiceGeneration;
        voiceHandler.postDelayed(new Runnable() {
            @Override public void run() { if (generation == voiceGeneration) beginVoiceSegment(); }
        }, delay);
    }

    private void stopVoiceInput() {
        if (!voiceActive) return;
        voiceStopping = true;
        if (recognizer == null) { endVoiceInput(""); return; }
        recognizer.stopListening();
        final int generation = voiceGeneration;
        voiceHandler.postDelayed(new Runnable() {
            @Override public void run() { if (generation == voiceGeneration && voiceStopping) endVoiceInput(""); }
        }, 1800);
    }

    private void endVoiceInput(String error) {
        if (!voiceActive) return;
        voiceActive = false;
        voiceStopping = false;
        voiceGeneration++;
        if (recognizer != null) { recognizer.cancel(); recognizer.destroy(); recognizer = null; }
        sendVoiceResult("", error, true);
    }

    private void sendVoiceResult(String text, String error, boolean ended) {
        String script = "window.dispatchEvent(new CustomEvent('rep-trainer-voice-result',{detail:{id:"
                + JSONObject.quote(voiceId) + ",text:" + JSONObject.quote(text) + ",error:"
                + JSONObject.quote(error) + ",ended:" + ended + "}}))";
        webView.evaluateJavascript(script, null);
    }

    private void sendSpeechError(String error) {
        final String script = "window.dispatchEvent(new CustomEvent('rep-trainer-speech-error',{detail:{error:"
                + JSONObject.quote(error) + "}}))";
        webView.post(new Runnable() {
            @Override
            public void run() { webView.evaluateJavascript(script, null); }
        });
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        webView.saveState(outState);
        super.onSaveInstanceState(outState);
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }

    @Override
    protected void onDestroy() {
        if (recognizer != null) { recognizer.cancel(); recognizer.destroy(); recognizer = null; }
        if (speech != null) { speech.stop(); speech.shutdown(); }
        webView.destroy();
        super.onDestroy();
    }
}
