from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

from .provider import LLMMessage, LLMProvider, LLMResult
from .usage import UsageTracker

Response = str | list[str] | Callable[[list[LLMMessage]], str]


def _approx_tokens(s: str) -> int:
    return max(1, len(s) // 2)


class MockLLM(LLMProvider):
    """确定性假模型：按 prompt_name 返回预设文本。
    - str：每次都返回它；list[str]：依次返回，耗尽后重复最后一个；callable：由 messages 计算。
    - 未配置的 prompt_name 返回 default（默认 "{}"）。calls 记录所有调用以便断言。
    """

    name = "mock"

    def __init__(self, responses: dict[str, Response] | None = None, default: str = "{}",
                 tracker: UsageTracker | None = None):
        super().__init__(tracker or UsageTracker())   # 独立内存 tracker，不污染全局
        self.responses: dict[str, Response] = dict(responses or {})
        self.default = default
        self.calls: list[dict] = []
        self._idx: dict[str, int] = defaultdict(int)

    def set(self, prompt_name: str, value: Response) -> None:
        self.responses[prompt_name] = value
        self._idx[prompt_name] = 0

    def _complete(self, *, prompt_name, system, messages, temperature, json_mode, max_tokens) -> LLMResult:
        self.calls.append({"prompt_name": prompt_name, "system": system, "messages": list(messages),
                           "json_mode": json_mode})
        v = self.responses.get(prompt_name, self.default)
        if callable(v):
            text = v(messages)
        elif isinstance(v, list):
            i = self._idx[prompt_name]
            text = v[min(i, len(v) - 1)]
            self._idx[prompt_name] += 1
        else:
            text = v
        pt = _approx_tokens(system + "".join(m["content"] for m in messages))
        return LLMResult(text=text, prompt_tokens=pt, completion_tokens=_approx_tokens(text))
