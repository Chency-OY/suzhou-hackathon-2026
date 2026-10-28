from functools import lru_cache

from .db import Repo
from .llm import get_provider as _make_provider
from .rag import KnowledgeBase
from .sessions import SessionEngine, load_rules


@lru_cache
def get_repo() -> Repo:
    return Repo()


@lru_cache
def get_provider():
    return _make_provider()


@lru_cache
def get_kb():
    try:
        kb = KnowledgeBase()
        return kb if kb.count() > 0 else None
    except Exception:  # noqa: BLE001
        return None


@lru_cache
def get_engine() -> SessionEngine:
    return SessionEngine(get_provider(), get_kb(), load_rules())
