from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel

from .provider import LLMMessage, LLMProvider

T = TypeVar("T", bound=BaseModel)
log = logging.getLogger(__name__)
FENCE = "`" * 3


def extract_json(text: str) -> str:
    """从模型输出中提取第一个完整 JSON 对象/数组（容忍代码围栏与前后废话）。"""
    t = text.strip()
    if t.startswith(FENCE):
        t = re.sub(r"^" + FENCE + r"[a-zA-Z]*\s*", "", t)
        t = re.sub(FENCE + r"\s*$", "", t).strip()
    starts = [i for i in (t.find("{"), t.find("[")) if i != -1]
    if not starts:
        raise ValueError("no json found")
    start = min(starts)
    opener = t[start]
    closer = "}" if opener == "{" else "]"
    depth, in_str, esc = 0, False, False
    for i in range(start, len(t)):
        ch = t[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return t[start:i + 1]
    raise ValueError("unbalanced json")


def structured_call(provider: LLMProvider, *, prompt_name: str, system: str,
                    messages: list[LLMMessage], model_cls: type[T], fallback: T | Callable[[], T],
                    max_retries: int = 2, temperature: float = 0.3,
                    max_tokens: int | None = None) -> tuple[T, bool]:
    """调用 LLM 并按 model_cls 校验。失败重试至多 max_retries 次，仍失败返回 (fallback, True)。
    BudgetExceeded 等预算异常不在此处捕获，会向上抛出。"""
    msgs: list[LLMMessage] = list(messages)
    for attempt in range(max_retries + 1):
        res = provider.complete(prompt_name=prompt_name, system=system, messages=msgs,
                                temperature=temperature, json_mode=True, max_tokens=max_tokens)
        try:
            return model_cls.model_validate(json.loads(extract_json(res.text))), False
        except ValueError as e:   # json 解析错误与 pydantic ValidationError 均为 ValueError 子类
            log.warning("structured_call[%s] attempt %d failed: %s", prompt_name, attempt, str(e)[:200])
            msgs = msgs + [
                {"role": "assistant", "content": res.text},
                {"role": "user", "content": f"上一次输出无法解析或不符合要求：{str(e)[:300]}。"
                                            "请只输出符合要求的 JSON，不要输出任何其他文字。"},
            ]
    log.error("structured_call[%s] degraded to fallback", prompt_name)
    value = fallback() if callable(fallback) else fallback
    return value, True
