from functools import lru_cache

from .db import Repo
from .llm import get_provider as make_provider
from .rag import KnowledgeBase
from .sessions import SessionEngine, load_rules


@lru_cache
def get_repo() -> Repo:
    return Repo()


@lru_cache
def get_provider():
    return make_provider()


@lru_cache
def get_kb():
    try:
        kb = KnowledgeBase()
        return kb if kb.count() > 0 else None
    except Exception:  # noqa: BLE001 - knowledge base is optional in demo mode
        return None


@lru_cache
def get_engine() -> SessionEngine:
    return SessionEngine(get_provider(), get_kb(), load_rules())
