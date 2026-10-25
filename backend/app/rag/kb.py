from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .embedding import EmbeddingProvider, get_embedder
from .facts import Fact
from .store import VectorStore, get_store


@dataclass
class FactChunk:
    id: str
    text: str
    category: str
    verified: bool
    source: str
    caution: str
    kind: str          # "fact" | "label"
    score: float = 0.0


def chunk_label(text: str, max_len: int = 800) -> tuple[bool, list[str]]:
    """说明书分块：按标题切；front matter 含 `verified: true` 才视为已核验。"""
    verified = False
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if m:
        verified = bool(re.search(r"^verified:\s*true\s*$", m.group(1), re.MULTILINE | re.IGNORECASE))
        text = text[m.end():]
    sections = re.split(r"\n(?=#{1,4}\s)", text.strip())
    chunks: list[str] = []
    for sec in sections:
        sec = sec.strip()
        if len(sec) < 20:
            continue
        if len(sec) <= max_len:
            chunks.append(sec)
            continue
        buf = ""
        for para in re.split(r"\n\s*\n", sec):
            if buf and len(buf) + len(para) > max_len:
                chunks.append(buf.strip())
                buf = ""
            buf += para + "\n\n"
        if buf.strip():
            chunks.append(buf.strip())
    return verified, chunks


class KnowledgeBase:
    def __init__(self, embedder: EmbeddingProvider | None = None, store: VectorStore | None = None):
        self.embedder = embedder or get_embedder()
        self.store = store or get_store()

    def reset(self) -> None:
        self.store.reset()

    def count(self) -> int:
        return self.store.count()

    def index_facts(self, facts: list[Fact]) -> int:
        if not facts:
            return 0
        texts = [f.statement + (f"（注意：{f.caution}）" if f.caution else "") for f in facts]
        metas = [{"category": f.category, "verified": f.verified, "source": f.source,
                  "caution": f.caution, "kind": "fact"} for f in facts]
        self.store.upsert([f.id for f in facts], self.embedder.embed(texts), texts, metas)
        return len(facts)

    def index_label(self, path: str | Path) -> int:
        verified, chunks = chunk_label(Path(path).read_text(encoding="utf-8"))
        if not chunks:
            return 0
        ids = [f"label_{i:03d}" for i in range(len(chunks))]
        metas = [{"category": "label", "verified": verified, "source": "说明书(label.md)",
                  "caution": "", "kind": "label"} for _ in chunks]
        self.store.upsert(ids, self.embedder.embed(chunks), chunks, metas)
        return len(chunks)

    def retrieve(self, query: str, k: int = 5, only_verified: bool = False,
                 category: str | None = None) -> list[FactChunk]:
        where: dict = {}
        if only_verified:
            where["verified"] = True
        if category:
            where["category"] = category
        emb = self.embedder.embed([query])[0]
        return [FactChunk(id=h.id, text=h.document, category=h.metadata.get("category", ""),
                          verified=bool(h.metadata.get("verified", False)),
                          source=h.metadata.get("source", ""), caution=h.metadata.get("caution", ""),
                          kind=h.metadata.get("kind", "fact"), score=h.score)
                for h in self.store.query(emb, k, where or None)]
