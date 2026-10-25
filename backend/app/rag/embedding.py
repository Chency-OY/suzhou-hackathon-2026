from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod

import httpx

from ..config import settings

_CJK_RUN = re.compile(r"[\u4e00-\u9fff]+")
_WORD = re.compile(r"[a-z0-9][a-z0-9.%\-]*")


class EmbeddingProvider(ABC):
    dim: int = 0

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...


def _l2(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v] if n else v


class HashEmbedding(EmbeddingProvider):
    """离线、确定性的哈希词袋嵌入（中文用字与二字组）。用于测试与无嵌入服务时的兜底。"""

    def __init__(self, dim: int = 512):
        self.dim = dim

    def _tokens(self, text: str) -> list[tuple[str, float]]:
        t = text.lower()
        toks: list[tuple[str, float]] = [(w, 1.5) for w in _WORD.findall(t)]
        for run in _CJK_RUN.findall(t):
            toks += [(c, 0.3) for c in run]
            toks += [(run[i:i + 2], 1.0) for i in range(len(run) - 1)]
        return toks

    def embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for text in texts:
            v = [0.0] * self.dim
            for tok, w in self._tokens(text):
                h = int(hashlib.md5(tok.encode("utf-8")).hexdigest()[:8], 16)
                v[h % self.dim] += w if (h >> 16) & 1 == 0 else -w
            out.append(_l2(v))
        return out


class OpenAICompatEmbedding(EmbeddingProvider):
    def __init__(self):
        if not (settings.embed_base_url and settings.embed_api_key and settings.embed_model):
            raise RuntimeError("openai_compat 嵌入需要 EMBED_BASE_URL / EMBED_API_KEY / EMBED_MODEL")

    def embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        url = settings.embed_base_url.rstrip("/") + "/embeddings"
        headers = {"Authorization": f"Bearer {settings.embed_api_key}"}
        for i in range(0, len(texts), 16):
            r = httpx.post(url, json={"model": settings.embed_model, "input": texts[i:i + 16]},
                           headers=headers, timeout=60)
            r.raise_for_status()
            data = sorted(r.json()["data"], key=lambda d: d.get("index", 0))
            out += [_l2([float(x) for x in d["embedding"]]) for d in data]
        if out:
            self.dim = len(out[0])
        return out


def get_embedder() -> EmbeddingProvider:
    if settings.embed_provider == "hash":
        return HashEmbedding()
    if settings.embed_provider == "openai_compat":
        return OpenAICompatEmbedding()
    raise ValueError(f"未知的 EMBED_PROVIDER: {settings.embed_provider}")
