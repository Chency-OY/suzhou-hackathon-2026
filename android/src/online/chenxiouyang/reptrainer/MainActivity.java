package online.chenxiouyang.reptrainer;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.speech.RecognizerIntent;
import android.webkit.CookieManager;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import org.json.JSONObject;

import java.util.ArrayList;

public class MainActivity extends Activity {
    private static final int VOICE_REQUEST = 1001;
    private static final String HOME = "https://chenxi-ouyang.online/rep-trainer/diary";
    private WebView webView;

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
            startVoiceInput();
            return true;
        }
        if ("https".equals(uri.getScheme()) && "chenxi-ouyang.online".equals(uri.getHost())
                && uri.getPath() != null && uri.getPath().startsWith("/rep-trainer/")) return false;
        try { startActivity(new Intent(Intent.ACTION_VIEW, uri)); }
        catch (ActivityNotFoundException ignored) { }
        return true;
    }

    private void startVoiceInput() {
        Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "zh-CN");
        intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1);
        intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "请说出刚才的想法");
        try { startActivityForResult(intent, VOICE_REQUEST); }
        catch (ActivityNotFoundException ignored) {
            sendVoiceResult("", "手机未安装可用的语音识别服务，请用键盘输入。");
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != VOICE_REQUEST) return;
        if (resultCode == RESULT_OK && data != null) {
            ArrayList<String> results = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
            if (results != null && !results.isEmpty()) {
                sendVoiceResult(results.get(0), "");
                return;
            }
        }
        sendVoiceResult("", "语音输入已取消，可以继续口述或手动输入。");
    }

    private void sendVoiceResult(String text, String error) {
        String script = "window.dispatchEvent(new CustomEvent('rep-trainer-voice-result',{detail:{text:"
                + JSONObject.quote(text) + ",error:" + JSONObject.quote(error) + "}}))";
        webView.evaluateJavascript(script, null);
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
        webView.destroy();
        super.onDestroy();
    }
}
