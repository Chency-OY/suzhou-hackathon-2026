from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from ..config import settings

log = logging.getLogger(__name__)


@dataclass
class Hit:
    id: str
    document: str
    metadata: dict
    score: float


def _match(meta: dict, where: dict | None) -> bool:
    return all(meta.get(k) == v for k, v in (where or {}).items())


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, ids: list[str], embeddings: list[list[float]], documents: list[str],
               metadatas: list[dict]) -> None: ...

    @abstractmethod
    def query(self, embedding: list[float], k: int, where: dict | None = None) -> list[Hit]: ...

    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def reset(self) -> None: ...


class SimpleStore(VectorStore):
    """纯 Python 余弦检索（向量需已归一化）。几百条以内足够。可选 JSON 持久化。"""

    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else None
        self._items: dict[str, tuple[list[float], str, dict]] = {}
        if self.path and self.path.exists():
            for it in json.loads(self.path.read_text(encoding="utf-8"))["items"]:
                self._items[it["id"]] = (it["embedding"], it["document"], it["metadata"])

    def _save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        items = [{"id": i, "embedding": e, "document": d, "metadata": m}
                 for i, (e, d, m) in self._items.items()]
        self.path.write_text(json.dumps({"items": items}, ensure_ascii=False), encoding="utf-8")

    def upsert(self, ids, embeddings, documents, metadatas):
        for i, e, d, m in zip(ids, embeddings, documents, metadatas):
            self._items[i] = (e, d, m)
        self._save()

    def query(self, embedding, k, where=None):
        scored = []
        for i, (e, d, m) in self._items.items():
            if _match(m, where):
                scored.append(Hit(i, d, m, sum(a * b for a, b in zip(embedding, e))))
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:k]

    def count(self):
        return len(self._items)

    def reset(self):
        self._items.clear()
        if self.path and self.path.exists():
            self.path.unlink()


def _chroma_where(where: dict | None) -> dict | None:
    if not where:
        return None
    conds = [{k: v} for k, v in where.items()]
    return conds[0] if len(conds) == 1 else {"$and": conds}


class ChromaStore(VectorStore):
    def __init__(self, path: str, name: str = "kb_store"):
        # chromadb >= 1.x 要求集合名 3~512 个字符，参考实现的 "kb" 会被拒绝
        import chromadb

        self.name = name
        self.client = chromadb.PersistentClient(path=path)
        self.col = self.client.get_or_create_collection(name, metadata={"hnsw:space": "cosine"})

    def upsert(self, ids, embeddings, documents, metadatas):
        self.col.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    def query(self, embedding, k, where=None):
        n = min(k, self.col.count())
        if n == 0:
            return []
        res = self.col.query(query_embeddings=[embedding], n_results=n, where=_chroma_where(where))
        return [Hit(i, d, m, 1.0 - dist) for i, d, m, dist in
                zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0])]

    def count(self):
        return self.col.count()

    def reset(self):
        self.client.delete_collection(self.name)
        self.col = self.client.get_or_create_collection(self.name, metadata={"hnsw:space": "cosine"})


def get_store(kind: str | None = None, persist_dir: str | None = None) -> VectorStore:
    kind = kind or settings.vector_store
    persist = persist_dir or settings.chroma_dir
    if kind == "chroma":
        try:
            return ChromaStore(persist)
        except Exception as e:  # noqa: BLE001
            log.warning("Chroma 不可用（%s），回退到 SimpleStore", e)
            return SimpleStore(Path(persist) / "simple.json")
    if kind == "simple":
        return SimpleStore(Path(persist) / "simple.json")
    raise ValueError(f"未知的 VECTOR_STORE: {kind}")
