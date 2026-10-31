from __future__ import annotations

from datetime import UTC, datetime, timedelta

from ..api.radar import collect_radar
from ..db import Repo
from ..llm import LLMProvider
from ..models.radar import AcademicRadar

REFRESH_INTERVAL = timedelta(hours=24)


def refresh_due_radars(repo: Repo, owner_id: str, provider: LLMProvider, *, now: datetime | None = None,
                       limit: int = 3) -> list[AcademicRadar]:
    now = now or datetime.now(UTC)
    candidates = []
    for item in repo.list(AcademicRadar):
        if item.owner_id != owner_id or not item.auto_refresh:
            continue
        last = max(item.searched_at, item.last_auto_checked_at or item.searched_at)
        if now - last < REFRESH_INTERVAL:
            continue
        candidates.append((last, item))
    candidates.sort(key=lambda pair: pair[0])
    updated = []
    for _, item in candidates[:max(0, min(limit, 3))]:
        current = repo.get(AcademicRadar, item.id)
        if not current or not current.auto_refresh:
            continue
        try:
            result = collect_radar(repo, item.owner_id, item.doctor_name, item.hospital, provider, current)
            if result.searched_at <= current.searched_at:
                result.refresh_error = "自动更新暂不可用，已保留上次检索结果。"
        except Exception:  # noqa: BLE001 - preserve old results and continue other subscriptions
            result = current
            result.refresh_error = "自动更新暂不可用，已保留上次检索结果。"
        latest = repo.get(AcademicRadar, item.id)
        result.auto_refresh = latest.auto_refresh if latest else False
        result.last_auto_checked_at = now
        repo.save(result)
        updated.append(result)
    return updated
