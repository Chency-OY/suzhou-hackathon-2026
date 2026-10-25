from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..config import settings


@dataclass(frozen=True)
class Prompt:
    name: str
    version: str
    body: str

    def render(self, **kwargs: object) -> str:
        out = self.body
        for k, v in kwargs.items():
            out = out.replace("{{" + k + "}}", str(v))
        left = re.findall(r"\{\{(\w+)\}\}", out)
        if left:
            raise KeyError(f"prompt {self.name} 缺少变量: {sorted(set(left))}")
        return out


def load_prompt(name: str, prompts_dir: str | Path | None = None) -> Prompt:
    path = Path(prompts_dir or settings.prompts_dir) / f"{name}.md"
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        raise ValueError(f"{path} 缺少 front matter（需含 version:）")
    meta = dict(
        line.split(":", 1) for line in m.group(1).splitlines() if ":" in line
    )
    version = meta.get("version", "").strip()
    if not version:
        raise ValueError(f"{path} 的 front matter 缺少 version")
    return Prompt(name=name, version=version, body=m.group(2).strip())
