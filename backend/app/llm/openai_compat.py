from __future__ import annotations

import time

import httpx

from ..config import settings
from .provider import LLMMessage, LLMProvider, LLMResult
from .usage import UsageTracker


class OpenAICompatProvider(LLMProvider):
    """任意兼容 POST {base}/chat/completions 的服务。"""

    name = "openai_compat"

    def __init__(self, tracker: UsageTracker | None = None):
        super().__init__(tracker)
        if not (settings.llm_base_url and settings.llm_api_key and settings.llm_model):
            raise RuntimeError("openai_compat 需要设置 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL")

    def _complete(self, *, prompt_name, system, messages: list[LLMMessage], temperature, json_mode,
                  max_tokens) -> LLMResult:
        payload: dict = {
            "model": settings.llm_model,
            "messages": [{"role": "system", "content": system}, *messages],
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if json_mode and settings.llm_json_mode:
            payload["response_format"] = {"type": "json_object"}
        url = settings.llm_base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {settings.llm_api_key}"}

        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                r = httpx.post(url, json=payload, headers=headers, timeout=settings.llm_timeout_s)
                if r.status_code in (429, 500, 502, 503, 504):
                    raise httpx.HTTPStatusError("retryable", request=r.request, response=r)
                r.raise_for_status()
                data = r.json()
                usage = data.get("usage") or {}
                return LLMResult(
                    text=data["choices"][0]["message"].get("content") or "",
                    prompt_tokens=int(usage.get("prompt_tokens", 0)),
                    completion_tokens=int(usage.get("completion_tokens", 0)),
                )
            except (httpx.HTTPError, KeyError, ValueError) as e:
                last_exc = e
                time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"LLM 调用失败（{prompt_name}）：{last_exc}")
