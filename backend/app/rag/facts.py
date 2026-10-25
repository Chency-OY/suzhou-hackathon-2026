from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class Fact(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    statement: str = Field(min_length=5)
    source: str = ""
    source_url: str = ""
    verified: bool = False
    caution: str = ""


def read_raw(path: str | Path) -> list[dict]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("facts", [])
    if not isinstance(data, list):
        # 数据格式错误用 ValueError（保持参考实现行为）；ruff TRY004 建议改 TypeError，不采纳
        raise ValueError("facts.yaml 顶层必须是列表，或含 facts 键的字典")  # noqa: TRY004
    return data


def load_facts(path: str | Path) -> tuple[list[Fact], list[str]]:
    """返回 (合法条目, 错误列表)。重复 id 只保留第一条并报错。"""
    errors: list[str] = []
    facts: list[Fact] = []
    seen: set[str] = set()
    try:
        raw = read_raw(path)
    except Exception as e:  # noqa: BLE001
        return [], [f"无法读取 {path}: {e}"]
    for i, item in enumerate(raw):
        try:
            f = Fact.model_validate(item)
        except ValidationError as e:
            errors.append(f"第 {i + 1} 条无效: {str(e)[:200]}")
            continue
        if f.id in seen:
            errors.append(f"重复 id: {f.id}")
            continue
        seen.add(f.id)
        facts.append(f)
    return facts, errors
