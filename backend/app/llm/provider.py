from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypedDict

from .usage import UsageTracker, get_tracker


class LLMMessage(TypedDict):
    role: str      # "user" | "assistant"
    content: str


@dataclass
class LLMResult:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    degraded: bool = False


class LLMProvider(ABC):
    """所有业务代码只依赖此抽象。complete() 统一做预算检查与用量记录。"""

    name = "base"

    def __init__(self, tracker: UsageTracker | None = None):
        self.tracker = tracker or get_tracker()

    def complete(self, *, prompt_name: str, system: str, messages: list[LLMMessage],
                 temperature: float = 0.7, json_mode: bool = False,
                 max_tokens: int | None = None) -> LLMResult:
        self.tracker.check_budget()
        t0 = time.time()
        res = self._complete(prompt_name=prompt_name, system=system, messages=messages,
                             temperature=temperature, json_mode=json_mode, max_tokens=max_tokens)
        self.tracker.record(prompt_name, res.prompt_tokens, res.completion_tokens,
                            elapsed_s=time.time() - t0, degraded=res.degraded)
        return res

    @abstractmethod
    def _complete(self, *, prompt_name: str, system: str, messages: list[LLMMessage],
                  temperature: float, json_mode: bool, max_tokens: int | None) -> LLMResult: ...
