from __future__ import annotations

import json
import threading
from collections import defaultdict
from datetime import UTC, date, datetime
from pathlib import Path


class BudgetExceeded(RuntimeError):
    pass


class UsageTracker:
    """记录每次 LLM 调用的 token 用量；daily_cap>0 时超限抛 BudgetExceeded。"""

    def __init__(self, log_dir: Path | None = None, daily_cap: int = 0):
        self.log_dir = Path(log_dir) if log_dir else None
        self.daily_cap = daily_cap
        self._lock = threading.Lock()
        self._by_prompt: dict[str, dict[str, int]] = defaultdict(
            lambda: {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0})
        self._day = date.today()
        self._today_total = 0
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self._today_total = self._load_today_total()

    def _file(self) -> Path:
        return self.log_dir / f"{self._day.isoformat()}.jsonl"  # type: ignore[operator]

    def _load_today_total(self) -> int:
        f = self._file()
        if not f.exists():
            return 0
        total = 0
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(line)
                total += d.get("prompt_tokens", 0) + d.get("completion_tokens", 0)
            except json.JSONDecodeError:
                continue
        return total

    def _roll(self) -> None:
        if date.today() != self._day:
            self._day = date.today()
            self._today_total = self._load_today_total() if self.log_dir else 0

    @property
    def today_total(self) -> int:
        with self._lock:
            self._roll()
            return self._today_total

    def check_budget(self) -> None:
        if self.daily_cap > 0 and self.today_total >= self.daily_cap:
            raise BudgetExceeded(f"daily token cap reached: {self.today_total}/{self.daily_cap}")

    def record(self, prompt_name: str, prompt_tokens: int, completion_tokens: int,
               elapsed_s: float = 0.0, degraded: bool = False) -> None:
        with self._lock:
            self._roll()
            agg = self._by_prompt[prompt_name]
            agg["calls"] += 1
            agg["prompt_tokens"] += prompt_tokens
            agg["completion_tokens"] += completion_tokens
            self._today_total += prompt_tokens + completion_tokens
            if self.log_dir:
                row = {"ts": datetime.now(UTC).isoformat(), "prompt": prompt_name,
                       "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
                       "elapsed_s": round(elapsed_s, 3), "degraded": degraded}
                with self._file().open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def summary(self) -> dict[str, dict[str, int]]:
        with self._lock:
            return {k: dict(v) for k, v in self._by_prompt.items()}


_tracker: UsageTracker | None = None


def get_tracker() -> UsageTracker:
    global _tracker
    if _tracker is None:
        from ..config import settings
        _tracker = UsageTracker(Path(settings.usage_dir), settings.daily_token_cap)
    return _tracker
