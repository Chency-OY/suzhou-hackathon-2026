from functools import lru_cache

from .db import Repo


@lru_cache
def get_repo() -> Repo:
    return Repo()
