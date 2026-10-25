# TASKS_T1-T3.md — Codex 可直接执行的阶段任务书

适用范围：`SPEC.md` 第 9 节 Day 1 的 **T1、T2、T3**。
目标：按本文档逐步执行，完成后仓库应能 `make setup && make test` 全绿，且 `make dev` 可启动并访问 `/api/health`。

---

## 0. 执行规则（先读）

1. 先阅读仓库根目录的 `AGENTS.md` 与 `SPEC.md`（第 3、5、6、7 节）。**不得修改这两个文件。**
2. 严格按 T1 → T2 → T3 顺序执行；每个任务结束跑一次 `make test`，通过后再提交，提交信息格式 `[T1] ...`。
3. **不要做 T4 及之后的内容**（不装 ChromaDB、不写 RAG、不做画像生成、不写业务 API、不做前端页面）。
4. 测试中**禁止调用真实 LLM 或联网**，一律使用 `MockLLM`。
5. 遇到文档未覆盖的细节：按"最保守、最简单"的假设继续，并在 `docs/QUESTIONS.md` 追加一条记录（格式：日期 | 任务编号 | 问题 | 采用的假设）。不要停下来提问。
6. 本文档中的代码是**参考实现**：可以修正明显错误或适配版本差异，但**对外接口（函数名、参数名、字段名、文件路径）必须保持一致**，后续任务会依赖它们。
7. 所有文件使用 UTF-8；Python 代码风格以 `ruff` 默认规则为准。

## 1. 交付物总览（完成后必须全部存在）

```
AGENTS.md  SPEC.md  TASKS_T1-T3.md          # 已有，勿改
Makefile  pyproject.toml  .env.example  .gitignore
scripts/ci.sh  scripts/verify_t1_t3.sh
docs/PROGRESS.md  docs/QUESTIONS.md
prompts/CHANGELOG.md  prompts/_example.md
data/{sources,kb,personas,scenarios,rubric,calibration,usage}/.gitkeep
backend/app/__init__.py  backend/app/main.py  backend/app/config.py  backend/app/db.py
backend/app/api/__init__.py
backend/app/models/__init__.py  backend/app/models/constants.py  backend/app/models/domain.py
backend/app/llm/__init__.py  backend/app/llm/provider.py  backend/app/llm/mock.py
backend/app/llm/openai_compat.py  backend/app/llm/factory.py  backend/app/llm/structured.py
backend/app/llm/usage.py  backend/app/llm/prompts.py
backend/app/{rag,personas,sessions,scoring,compliance,playbook}/__init__.py
backend/tests/__init__.py  backend/tests/factories.py
backend/tests/test_health.py  backend/tests/test_models.py  backend/tests/test_db.py
backend/tests/test_llm.py  backend/tests/test_prompts.py
frontend/.gitkeep
```

---

## 2. T1 — 仓库初始化

### 2.1 创建目录
```bash
mkdir -p backend/app/{api,models,llm,rag,personas,sessions,scoring,compliance,playbook} backend/tests
mkdir -p data/{sources,kb,personas,scenarios,rubric,calibration,usage} prompts scripts docs frontend
for d in data/sources data/kb data/personas data/scenarios data/rubric data/calibration data/usage frontend; do touch $d/.gitkeep; done
for d in rag personas sessions scoring compliance playbook api; do touch backend/app/$d/__init__.py; done
touch backend/app/__init__.py backend/tests/__init__.py
```

### 2.2 `pyproject.toml`
```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "rep-trainer"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.110",
  "uvicorn[standard]>=0.29",
  "pydantic>=2.6",
  "pydantic-settings>=2.2",
  "sqlmodel>=0.0.16",
  "httpx>=0.27",
  "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = ["pytest>=8", "ruff>=0.4"]

[tool.setuptools.packages.find]
where = ["backend"]
include = ["app*"]

[tool.pytest.ini_options]
testpaths = ["backend/tests"]
pythonpath = ["backend"]

[tool.ruff]
line-length = 110
target-version = "py311"
```
> 注意：此阶段**不要**添加 chromadb 等重依赖，T4 再加。

### 2.3 `Makefile`（缩进必须是 TAB）
```make
.PHONY: setup dev test lint seed gen-personas
PY ?= python3
VENV = . .venv/bin/activate

setup:
	$(PY) -m venv .venv
	$(VENV) && pip install -U pip && pip install -e ".[dev]"
	@if [ -f frontend/package.json ]; then cd frontend && pnpm install; fi

dev:
	$(VENV) && uvicorn app.main:app --app-dir backend --reload --port 8000

test:
	$(VENV) && pytest -q
	@if [ -f frontend/package.json ]; then cd frontend && pnpm exec tsc --noEmit; fi

lint:
	$(VENV) && ruff check backend

seed:
	@echo "seed: 将在 T4 实现"

gen-personas:
	@echo "gen-personas: 将在 T5 实现 (N=$(N))"
```

### 2.4 `.env.example`
```dotenv
# LLM：mock | openai_compat
LLM_PROVIDER=mock
# 以下仅 openai_compat 使用（任意兼容 /chat/completions 的服务）
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
LLM_JSON_MODE=true
LLM_TIMEOUT_S=90
# 每日 token 上限，0 表示不限制
DAILY_TOKEN_CAP=0
USAGE_DIR=data/usage
DB_URL=sqlite:///./data/app.db
PROMPTS_DIR=prompts
```

### 2.5 `.gitignore`
```gitignore
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.env
data/app.db
data/usage/*.jsonl
data/chroma/
node_modules/
frontend/dist/
```

### 2.6 `scripts/ci.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
make lint
make test
```
执行 `chmod +x scripts/ci.sh scripts/verify_t1_t3.sh`。

### 2.7 文档与 prompts 占位
`docs/PROGRESS.md`：
```markdown
# 进度记录
| 日期 | 任务 | 状态 | 已知问题 |
|---|---|---|---|
```
`docs/QUESTIONS.md`：
```markdown
# 待确认问题
| 日期 | 任务 | 问题 | 采用的假设 |
|---|---|---|---|
```
`prompts/CHANGELOG.md`：
```markdown
# Prompt 变更记录
格式：日期 | 文件 | 版本 | 变更说明
```
`prompts/_example.md`：
```markdown
---
version: 0.1.0
---
你是一个测试助手。输入内容：{{text}}
只输出 JSON：{"echo": "<原样返回输入内容>"}
```

### 2.8 `backend/app/config.py`
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "mock"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_json_mode: bool = True
    llm_timeout_s: float = 90.0
    daily_token_cap: int = 0
    usage_dir: str = "data/usage"
    db_url: str = "sqlite:///./data/app.db"
    prompts_dir: str = "prompts"


settings = Settings()
```

### 2.9 `backend/app/main.py`
```python
from fastapi import FastAPI

from .config import settings

app = FastAPI(title="Rep Trainer")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "llm_provider": settings.llm_provider}
```

### 2.10 `backend/tests/test_health.py`
```python
from fastapi.testclient import TestClient

from app.main import app


def test_health():
    r = TestClient(app).get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
```

### 2.11 T1 验收
```bash
make setup && make lint && make test && git add -A && git commit -m "[T1] repo skeleton"
```
`make test` 中 `test_health` 通过；`make dev` 启动后 `curl localhost:8000/api/health` 返回 `{"status":"ok",...}`。

---

## 3. T2 — 领域模型与持久化

### 3.1 `backend/app/models/constants.py`
```python
DIMENSIONS = (
    "opening",             # 开场与目标设定
    "discovery",           # 需求探寻
    "product_evidence",    # 产品信息与证据运用
    "objection_handling",  # 异议处理
    "closing",             # 促成与下一步
    "communication",       # 沟通表达
)

DIMENSION_WEIGHTS = {
    "opening": 10,
    "discovery": 20,
    "product_evidence": 25,
    "objection_handling": 20,
    "closing": 10,
    "communication": 15,
}

DIMENSION_LABELS = {
    "opening": "开场与目标设定",
    "discovery": "需求探寻",
    "product_evidence": "产品信息与证据运用",
    "objection_handling": "异议处理",
    "closing": "促成与下一步",
    "communication": "沟通表达",
}

SIGNALS = (
    "relevant_to_concern", "asked_open_question", "cited_evidence", "empathy_shown",
    "addressed_objection", "vague_or_generic", "pushy", "exaggeration",
    "off_label_claim", "competitor_bashing", "ignored_doctor_question", "proposed_next_step",
)

assert sum(DIMENSION_WEIGHTS.values()) == 100
```

### 3.2 `backend/app/models/domain.py`
```python
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .constants import DIMENSION_WEIGHTS

Department = Literal["endocrinology", "cardiology", "hepatology"]
Difficulty = Literal["easy", "normal", "hard"]
Title = Literal["主任医师", "副主任医师", "主治医师"]
HospitalTier = Literal["三甲", "二级", "社区"]
Style = Literal["rigorous_evidence", "busy_efficient", "skeptical_challenger",
                "friendly_open", "conservative_habit"]
Concern = Literal["efficacy", "safety_gi", "price_access", "long_term_evidence",
                  "patient_adherence", "competitor_comparison", "cv_benefit"]
Trap = Literal["off_label_bait", "competitor_bash_bait", "exaggeration_bait", "none"]
ScenarioType = Literal["first_visit", "post_conference", "safety_concern", "competitor_compare",
                       "time_pressure", "revisit_after_rejection", "off_label_bait"]
Signal = Literal[
    "relevant_to_concern", "asked_open_question", "cited_evidence", "empathy_shown",
    "addressed_objection", "vague_or_generic", "pushy", "exaggeration",
    "off_label_claim", "competitor_bashing", "ignored_doctor_question", "proposed_next_step",
]
EndReason = Literal["agreed_next_step", "doctor_left", "time_up", "rep_ended"]
FindingKind = Literal["strength", "issue", "missed_opportunity", "compliance_violation"]


class DoctorPersona(BaseModel):
    id: str
    department: Department
    title: Title
    hospital_tier: HospitalTier
    style: Style
    concerns: list[Concern] = Field(min_length=1)
    current_habit: str
    hidden_objection: str
    time_budget_turns: int = Field(ge=3, le=12)
    initial_trust: int = Field(ge=0, le=100)
    initial_patience: int = Field(ge=0, le=100)
    traps: list[Trap] = Field(default_factory=lambda: ["none"])
    backstory: str
    speech_habits: str
    difficulty: Difficulty


class Scenario(BaseModel):
    id: str
    type: ScenarioType
    persona_id: str
    rep_goal: str
    context_brief: str
    opening_line: str
    success_criteria: list[str] = Field(default_factory=list)
    source: Literal["generated", "playbook"] = "generated"


class DoctorState(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    trust: int = 50
    patience: int = 50
    engagement: int = 50
    revealed_hidden_objection: bool = False

    @field_validator("trust", "patience", "engagement", mode="before")
    @classmethod
    def _clamp(cls, v):
        return max(0, min(100, int(v)))


class Turn(BaseModel):
    idx: int = Field(ge=0)
    speaker: Literal["rep", "doctor"]
    text: str
    signals: list[Signal] = Field(default_factory=list)
    state_after: DoctorState | None = None


class Session(BaseModel):
    id: str
    scenario_id: str
    rep_id: str
    started_at: datetime
    ended_at: datetime | None = None
    end_reason: EndReason | None = None
    turns: list[Turn] = Field(default_factory=list)


class Finding(BaseModel):
    turn_idx: int = Field(ge=0)
    kind: FindingKind
    dimension: str
    quote: str = Field(min_length=1)
    explanation: str
    better_version: str | None = None


class Report(BaseModel):
    id: str
    session_id: str
    dimension_scores: dict[str, int]
    total_score: int = Field(ge=0, le=100)
    raw_total: int = Field(ge=0, le=100)
    capped_by_compliance: bool = False
    findings: list[Finding] = Field(default_factory=list)
    summary: str = ""
    next_practice_tips: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_scores(self):
        for k, v in self.dimension_scores.items():
            if k not in DIMENSION_WEIGHTS:
                raise ValueError(f"unknown dimension: {k}")
            if not 0 <= v <= DIMENSION_WEIGHTS[k]:
                raise ValueError(f"score out of range for {k}: {v}")
        return self

    def drop_invalid_findings(self, turns: list[Turn]) -> tuple["Report", int]:
        """丢弃 quote 不在对应回合原文中的 Finding（防止幻觉定位）。返回(新报告, 丢弃数量)。"""
        by_idx = {t.idx: t.text for t in turns}
        kept = [f for f in self.findings if f.turn_idx in by_idx and f.quote in by_idx[f.turn_idx]]
        return self.model_copy(update={"findings": kept}), len(self.findings) - len(kept)


class PlaybookCard(BaseModel):
    id: str
    title: str
    applicable_scenario_types: list[ScenarioType]
    applicable_departments: list[Department]
    situation: str
    effective_response_pattern: str
    example_lines: list[str] = Field(default_factory=list, max_length=3)
    evidence_session_ids: list[str] = Field(default_factory=list)
    avg_score_of_source: float = 0.0
    status: Literal["candidate", "approved"] = "candidate"
```

### 3.3 `backend/app/models/__init__.py`
```python
from .constants import DIMENSION_LABELS, DIMENSION_WEIGHTS, DIMENSIONS, SIGNALS
from .domain import (DoctorPersona, DoctorState, Finding, PlaybookCard, Report, Scenario,
                     Session, Turn)

__all__ = [
    "DIMENSIONS", "DIMENSION_WEIGHTS", "DIMENSION_LABELS", "SIGNALS",
    "DoctorPersona", "DoctorState", "Finding", "PlaybookCard", "Report", "Scenario",
    "Session", "Turn",
]
```

### 3.4 `backend/app/db.py`
通用"类型 + id → JSON"存储，避免每加一个模型就改表结构。
```python
from __future__ import annotations

from datetime import datetime
from typing import TypeVar

from pydantic import BaseModel
from sqlmodel import Field, SQLModel, create_engine, select
from sqlmodel import Session as DBSession

from .config import settings

M = TypeVar("M", bound=BaseModel)


class Record(SQLModel, table=True):
    kind: str = Field(primary_key=True)
    id: str = Field(primary_key=True)
    data: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Repo:
    def __init__(self, url: str | None = None):
        self.engine = create_engine(url or settings.db_url, connect_args={"check_same_thread": False})
        SQLModel.metadata.create_all(self.engine)

    def save(self, obj: BaseModel) -> None:
        with DBSession(self.engine) as s:
            s.merge(Record(kind=type(obj).__name__, id=obj.id, data=obj.model_dump_json()))  # type: ignore[attr-defined]
            s.commit()

    def get(self, cls: type[M], id: str) -> M | None:
        with DBSession(self.engine) as s:
            rec = s.get(Record, (cls.__name__, id))
            return cls.model_validate_json(rec.data) if rec else None

    def list(self, cls: type[M], limit: int | None = None) -> list[M]:
        with DBSession(self.engine) as s:
            stmt = select(Record).where(Record.kind == cls.__name__).order_by(Record.id)
            if limit:
                stmt = stmt.limit(limit)
            return [cls.model_validate_json(r.data) for r in s.exec(stmt).all()]

    def delete(self, cls: type[BaseModel], id: str) -> bool:
        with DBSession(self.engine) as s:
            rec = s.get(Record, (cls.__name__, id))
            if not rec:
                return False
            s.delete(rec)
            s.commit()
            return True
```

### 3.5 `backend/tests/factories.py`
```python
from datetime import datetime

from app.models import DoctorPersona, Scenario, Session, Turn


def make_persona(**kw) -> DoctorPersona:
    base = dict(
        id="persona_001", department="endocrinology", title="副主任医师", hospital_tier="三甲",
        style="skeptical_challenger", concerns=["efficacy", "competitor_comparison"],
        current_habit="一线多用司美格鲁肽，对新药观望", hidden_objection="担心患者长期依从性和价格",
        time_budget_turns=6, initial_trust=40, initial_patience=60, traps=["none"],
        backstory="门诊以肥胖合并 2 型糖尿病患者为主。", speech_habits="爱打断，常说“你直接说重点”。",
        difficulty="hard",
    )
    base.update(kw)
    return DoctorPersona(**base)


def make_scenario(**kw) -> Scenario:
    base = dict(
        id="scn_001", type="first_visit", persona_id="persona_001", rep_goal="让医生了解产品并约下次沟通",
        context_brief="首次拜访内分泌科副主任。", opening_line="我只有几分钟，你说吧。",
        success_criteria=["探寻到医生关注点", "提出具体下一步"],
    )
    base.update(kw)
    return Scenario(**base)


def make_session(**kw) -> Session:
    base = dict(
        id="sess_001", scenario_id="scn_001", rep_id="rep_001", started_at=datetime(2026, 10, 25, 9, 0),
        turns=[
            Turn(idx=0, speaker="doctor", text="我只有几分钟，你说吧。"),
            Turn(idx=1, speaker="rep", text="张主任您好，我想先了解一下您门诊肥胖患者的用药情况。",
                 signals=["asked_open_question"]),
        ],
    )
    base.update(kw)
    return Session(**base)
```

### 3.6 `backend/tests/test_models.py`
```python
import pytest
from pydantic import ValidationError

from app.models import DoctorState, Finding, Report
from tests.factories import make_persona, make_session


def test_persona_bounds():
    with pytest.raises(ValidationError):
        make_persona(time_budget_turns=2)
    with pytest.raises(ValidationError):
        make_persona(initial_trust=101)
    with pytest.raises(ValidationError):
        make_persona(concerns=[])


def test_state_clamps_on_init_and_assignment():
    s = DoctorState(trust=150, patience=-5, engagement=50)
    assert (s.trust, s.patience) == (100, 0)
    s.trust += 200
    assert s.trust == 100
    s.engagement -= 999
    assert s.engagement == 0


def test_report_rejects_bad_scores():
    with pytest.raises(ValidationError):
        Report(id="r", session_id="s", dimension_scores={"opening": 11}, total_score=10, raw_total=10)
    with pytest.raises(ValidationError):
        Report(id="r", session_id="s", dimension_scores={"nope": 1}, total_score=1, raw_total=1)


def test_report_drops_hallucinated_quotes():
    sess = make_session()
    good = Finding(turn_idx=1, kind="strength", dimension="discovery", quote="了解一下您门诊肥胖患者",
                   explanation="开放式提问")
    bad = Finding(turn_idx=1, kind="issue", dimension="closing", quote="这句话原文里没有", explanation="x")
    oob = Finding(turn_idx=99, kind="issue", dimension="closing", quote="任意", explanation="x")
    rep = Report(id="r", session_id="s", dimension_scores={"discovery": 15}, total_score=15, raw_total=15,
                 findings=[good, bad, oob])
    new, dropped = rep.drop_invalid_findings(sess.turns)
    assert dropped == 2 and len(new.findings) == 1 and new.findings[0].quote == good.quote
```

### 3.7 `backend/tests/test_db.py`
```python
from app.db import Repo
from app.models import DoctorPersona, Scenario, Session
from tests.factories import make_persona, make_scenario, make_session


def test_roundtrip_and_upsert(tmp_path):
    repo = Repo(f"sqlite:///{tmp_path}/t.db")
    p = make_persona()
    repo.save(p)
    assert repo.get(DoctorPersona, p.id) == p
    repo.save(make_persona(current_habit="已更新"))      # 同 id 覆盖
    assert repo.get(DoctorPersona, p.id).current_habit == "已更新"
    assert len(repo.list(DoctorPersona)) == 1


def test_session_with_turns_roundtrip(tmp_path):
    repo = Repo(f"sqlite:///{tmp_path}/t.db")
    s = make_session()
    repo.save(s)
    got = repo.get(Session, s.id)
    assert got == s and got.turns[1].signals == ["asked_open_question"]


def test_kinds_are_isolated_and_delete(tmp_path):
    repo = Repo(f"sqlite:///{tmp_path}/t.db")
    repo.save(make_persona())
    repo.save(make_scenario())
    assert len(repo.list(DoctorPersona)) == 1 and len(repo.list(Scenario)) == 1
    assert repo.delete(Scenario, "scn_001") is True
    assert repo.delete(Scenario, "scn_001") is False
    assert repo.get(Scenario, "scn_001") is None
```

### 3.8 T2 验收
`make test` 通过；提交 `[T2] domain models and repo`。

---

## 4. T3 — LLM 抽象、MockLLM、结构化输出、预算闸门、Prompt 加载

### 4.1 追加依赖
无需新增（httpx、pyyaml 已在 T1 依赖中）。

### 4.2 `backend/app/llm/usage.py`
```python
from __future__ import annotations

import json
import threading
from collections import defaultdict
from datetime import date, datetime
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
                row = {"ts": datetime.utcnow().isoformat(), "prompt": prompt_name,
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
```

### 4.3 `backend/app/llm/provider.py`
```python
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypedDict

from .usage import UsageTracker, get_tracker


class LLMMessage(TypedDict):
    role: str      # "user" | "assistant"
    content: str


@dataclass
class LLMResult:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    degraded: bool = False


class LLMProvider(ABC):
    """所有业务代码只依赖此抽象。complete() 统一做预算检查与用量记录。"""

    name = "base"

    def __init__(self, tracker: UsageTracker | None = None):
        self.tracker = tracker or get_tracker()

    def complete(self, *, prompt_name: str, system: str, messages: list[LLMMessage],
                 temperature: float = 0.7, json_mode: bool = False,
                 max_tokens: int | None = None) -> LLMResult:
        self.tracker.check_budget()
        t0 = time.time()
        res = self._complete(prompt_name=prompt_name, system=system, messages=messages,
                             temperature=temperature, json_mode=json_mode, max_tokens=max_tokens)
        self.tracker.record(prompt_name, res.prompt_tokens, res.completion_tokens,
                            elapsed_s=time.time() - t0, degraded=res.degraded)
        return res

    @abstractmethod
    def _complete(self, *, prompt_name: str, system: str, messages: list[LLMMessage],
                  temperature: float, json_mode: bool, max_tokens: int | None) -> LLMResult: ...
```

### 4.4 `backend/app/llm/mock.py`
```python
from __future__ import annotations

from collections import defaultdict
from typing import Callable

from .provider import LLMMessage, LLMProvider, LLMResult
from .usage import UsageTracker

Response = str | list[str] | Callable[[list[LLMMessage]], str]


def _approx_tokens(s: str) -> int:
    return max(1, len(s) // 2)


class MockLLM(LLMProvider):
    """确定性假模型：按 prompt_name 返回预设文本。
    - str：每次都返回它；list[str]：依次返回，耗尽后重复最后一个；callable：由 messages 计算。
    - 未配置的 prompt_name 返回 default（默认 "{}"）。calls 记录所有调用以便断言。
    """

    name = "mock"

    def __init__(self, responses: dict[str, Response] | None = None, default: str = "{}",
                 tracker: UsageTracker | None = None):
        super().__init__(tracker or UsageTracker())   # 独立内存 tracker，不污染全局
        self.responses: dict[str, Response] = dict(responses or {})
        self.default = default
        self.calls: list[dict] = []
        self._idx: dict[str, int] = defaultdict(int)

    def set(self, prompt_name: str, value: Response) -> None:
        self.responses[prompt_name] = value
        self._idx[prompt_name] = 0

    def _complete(self, *, prompt_name, system, messages, temperature, json_mode, max_tokens) -> LLMResult:
        self.calls.append({"prompt_name": prompt_name, "system": system, "messages": list(messages),
                           "json_mode": json_mode})
        v = self.responses.get(prompt_name, self.default)
        if callable(v):
            text = v(messages)
        elif isinstance(v, list):
            i = self._idx[prompt_name]
            text = v[min(i, len(v) - 1)]
            self._idx[prompt_name] += 1
        else:
            text = v
        pt = _approx_tokens(system + "".join(m["content"] for m in messages))
        return LLMResult(text=text, prompt_tokens=pt, completion_tokens=_approx_tokens(text))
```

### 4.5 `backend/app/llm/openai_compat.py`
```python
from __future__ import annotations

import time

import httpx

from ..config import settings
from .provider import LLMMessage, LLMProvider, LLMResult
from .usage import UsageTracker


class OpenAICompatProvider(LLMProvider):
    """任意兼容 POST {base}/chat/completions 的服务。"""

    name = "openai_compat"

    def __init__(self, tracker: UsageTracker | None = None):
        super().__init__(tracker)
        if not (settings.llm_base_url and settings.llm_api_key and settings.llm_model):
            raise RuntimeError("openai_compat 需要设置 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL")

    def _complete(self, *, prompt_name, system, messages: list[LLMMessage], temperature, json_mode,
                  max_tokens) -> LLMResult:
        payload: dict = {
            "model": settings.llm_model,
            "messages": [{"role": "system", "content": system}, *messages],
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if json_mode and settings.llm_json_mode:
            payload["response_format"] = {"type": "json_object"}
        url = settings.llm_base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {settings.llm_api_key}"}

        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                r = httpx.post(url, json=payload, headers=headers, timeout=settings.llm_timeout_s)
                if r.status_code in (429, 500, 502, 503, 504):
                    raise httpx.HTTPStatusError("retryable", request=r.request, response=r)
                r.raise_for_status()
                data = r.json()
                usage = data.get("usage") or {}
                return LLMResult(
                    text=data["choices"][0]["message"].get("content") or "",
                    prompt_tokens=int(usage.get("prompt_tokens", 0)),
                    completion_tokens=int(usage.get("completion_tokens", 0)),
                )
            except (httpx.HTTPError, KeyError, ValueError) as e:
                last_exc = e
                time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"LLM 调用失败（{prompt_name}）：{last_exc}")
```

### 4.6 `backend/app/llm/factory.py`
```python
from ..config import settings
from .mock import MockLLM
from .provider import LLMProvider


def get_provider() -> LLMProvider:
    if settings.llm_provider == "mock":
        return MockLLM()
    if settings.llm_provider == "openai_compat":
        from .openai_compat import OpenAICompatProvider
        return OpenAICompatProvider()
    raise ValueError(f"未知的 LLM_PROVIDER: {settings.llm_provider}")
```

### 4.7 `backend/app/llm/structured.py`
```python
from __future__ import annotations

import json
import logging
import re
from typing import Callable, TypeVar

from pydantic import BaseModel

from .provider import LLMMessage, LLMProvider

T = TypeVar("T", bound=BaseModel)
log = logging.getLogger(__name__)
FENCE = "`" * 3


def extract_json(text: str) -> str:
    """从模型输出中提取第一个完整 JSON 对象/数组（容忍代码围栏与前后废话）。"""
    t = text.strip()
    if t.startswith(FENCE):
        t = re.sub(r"^" + FENCE + r"[a-zA-Z]*\s*", "", t)
        t = re.sub(FENCE + r"\s*$", "", t).strip()
    starts = [i for i in (t.find("{"), t.find("[")) if i != -1]
    if not starts:
        raise ValueError("no json found")
    start = min(starts)
    opener = t[start]
    closer = "}" if opener == "{" else "]"
    depth, in_str, esc = 0, False, False
    for i in range(start, len(t)):
        ch = t[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return t[start:i + 1]
    raise ValueError("unbalanced json")


def structured_call(provider: LLMProvider, *, prompt_name: str, system: str,
                    messages: list[LLMMessage], model_cls: type[T], fallback: T | Callable[[], T],
                    max_retries: int = 2, temperature: float = 0.3,
                    max_tokens: int | None = None) -> tuple[T, bool]:
    """调用 LLM 并按 model_cls 校验。失败重试至多 max_retries 次，仍失败返回 (fallback, True)。
    BudgetExceeded 等预算异常不在此处捕获，会向上抛出。"""
    msgs: list[LLMMessage] = list(messages)
    for attempt in range(max_retries + 1):
        res = provider.complete(prompt_name=prompt_name, system=system, messages=msgs,
                                temperature=temperature, json_mode=True, max_tokens=max_tokens)
        try:
            return model_cls.model_validate(json.loads(extract_json(res.text))), False
        except ValueError as e:   # json 解析错误与 pydantic ValidationError 均为 ValueError 子类
            log.warning("structured_call[%s] attempt %d failed: %s", prompt_name, attempt, str(e)[:200])
            msgs = msgs + [
                {"role": "assistant", "content": res.text},
                {"role": "user", "content": f"上一次输出无法解析或不符合要求：{str(e)[:300]}。"
                                            "请只输出符合要求的 JSON，不要输出任何其他文字。"},
            ]
    log.error("structured_call[%s] degraded to fallback", prompt_name)
    value = fallback() if callable(fallback) else fallback
    return value, True
```

### 4.8 `backend/app/llm/prompts.py`
```python
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
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        raise ValueError(f"{path} 缺少 front matter（需含 version:）")
    meta = dict(
        line.split(":", 1) for line in m.group(1).splitlines() if ":" in line
    )
    version = meta.get("version", "").strip()
    if not version:
        raise ValueError(f"{path} 的 front matter 缺少 version")
    return Prompt(name=name, version=version, body=m.group(2).strip())
```

### 4.9 `backend/app/llm/__init__.py`
```python
from .factory import get_provider
from .mock import MockLLM
from .prompts import Prompt, load_prompt
from .provider import LLMMessage, LLMProvider, LLMResult
from .structured import extract_json, structured_call
from .usage import BudgetExceeded, UsageTracker, get_tracker

__all__ = [
    "get_provider", "MockLLM", "Prompt", "load_prompt", "LLMMessage", "LLMProvider", "LLMResult",
    "extract_json", "structured_call", "BudgetExceeded", "UsageTracker", "get_tracker",
]
```

### 4.10 `backend/tests/test_llm.py`
```python
import pytest
from pydantic import BaseModel

from app.llm import BudgetExceeded, MockLLM, UsageTracker, extract_json, structured_call


class Out(BaseModel):
    ok: bool
    n: int


FALLBACK = Out(ok=False, n=-1)
MSG = [{"role": "user", "content": "hi"}]


def run(mock, **kw):
    return structured_call(mock, prompt_name="p", system="s", messages=MSG, model_cls=Out,
                           fallback=kw.pop("fallback", FALLBACK), **kw)


def test_valid_json():
    out, degraded = run(MockLLM({"p": '{"ok": true, "n": 1}'}))
    assert out == Out(ok=True, n=1) and degraded is False


def test_fenced_and_chatty_output():
    fence = "`" * 3
    out, degraded = run(MockLLM({"p": f'好的：\n{fence}json\n{{"ok": true, "n": 2}}\n{fence}\n谢谢'}))
    assert out.n == 2 and degraded is False


def test_retry_then_success():
    mock = MockLLM({"p": ["not json", '{"ok": true, "n": 3}']})
    out, degraded = run(mock)
    assert out.n == 3 and degraded is False
    assert len(mock.calls) == 2
    assert "无法解析" in mock.calls[1]["messages"][-1]["content"]   # 纠错提示已追加


def test_schema_violation_retries_then_falls_back():
    mock = MockLLM({"p": '{"ok": "maybe", "n": "x"}'})
    out, degraded = run(mock, max_retries=2)
    assert out == FALLBACK and degraded is True
    assert len(mock.calls) == 3


def test_callable_fallback():
    out, degraded = run(MockLLM({"p": "garbage"}), fallback=lambda: Out(ok=False, n=0), max_retries=0)
    assert degraded is True and out.n == 0


def test_extract_json_handles_braces_in_strings():
    assert extract_json('x {"a": "}{", "b": [1, {"c": 2}]} y') == '{"a": "}{", "b": [1, {"c": 2}]}'


def test_budget_guard_blocks_calls():
    tracker = UsageTracker(daily_cap=10)
    mock = MockLLM({"p": '{"ok": true, "n": 1}'}, tracker=tracker)
    tracker.record("seed", 8, 8)               # 已用 16 >= 10
    with pytest.raises(BudgetExceeded):
        run(mock)
    assert mock.calls == []                    # 超限时不应发起调用


def test_usage_recorded_and_persisted(tmp_path):
    tracker = UsageTracker(log_dir=tmp_path, daily_cap=0)
    mock = MockLLM({"p": '{"ok": true, "n": 1}'}, tracker=tracker)
    run(mock)
    assert tracker.summary()["p"]["calls"] == 1 and tracker.today_total > 0
    reloaded = UsageTracker(log_dir=tmp_path)   # 重启后可恢复当日累计
    assert reloaded.today_total == tracker.today_total
```

### 4.11 `backend/tests/test_prompts.py`
```python
import pytest

from app.llm import load_prompt


def test_load_and_render_example():
    p = load_prompt("_example", "prompts")
    assert p.version == "0.1.0"
    assert "你好" in p.render(text="你好")


def test_missing_variable_raises():
    with pytest.raises(KeyError):
        load_prompt("_example", "prompts").render()


def test_front_matter_required(tmp_path):
    (tmp_path / "bad.md").write_text("没有 front matter", encoding="utf-8")
    with pytest.raises(ValueError):
        load_prompt("bad", tmp_path)
```
> 说明：`pytest` 在仓库根目录运行，所以 `"prompts"` 相对路径有效。

### 4.12 T3 验收
`make lint && make test` 全绿；提交 `[T3] llm abstraction, mock, structured output, budget guard`。

---

## 5. 总验收脚本 `scripts/verify_t1_t3.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
missing=0
for f in AGENTS.md SPEC.md Makefile pyproject.toml .env.example .gitignore scripts/ci.sh \
  docs/PROGRESS.md docs/QUESTIONS.md prompts/CHANGELOG.md prompts/_example.md \
  backend/app/main.py backend/app/config.py backend/app/db.py \
  backend/app/models/constants.py backend/app/models/domain.py \
  backend/app/llm/provider.py backend/app/llm/mock.py backend/app/llm/openai_compat.py \
  backend/app/llm/factory.py backend/app/llm/structured.py backend/app/llm/usage.py \
  backend/app/llm/prompts.py backend/tests/test_models.py backend/tests/test_db.py \
  backend/tests/test_llm.py backend/tests/test_prompts.py backend/tests/test_health.py; do
  [ -f "$f" ] || { echo "MISSING: $f"; missing=1; }
done
[ "$missing" = 0 ] || exit 1
make lint
make test
. .venv/bin/activate
python - <<'PY'
import sys; sys.path.insert(0, "backend")
from app.models import DoctorPersona, Scenario, Session, Report, PlaybookCard, DoctorState, Turn, Finding
from app.llm import get_provider, MockLLM, structured_call, load_prompt, UsageTracker
from app.db import Repo
print("imports OK; provider =", get_provider().name)
PY
echo "T1-T3 VERIFIED"
```
期望输出末行：`T1-T3 VERIFIED`。

## 6. 完成后的汇报
1. 在 `docs/PROGRESS.md` 追加：
   ```
   | <日期> | T1 | 完成 | |
   | <日期> | T2 | 完成 | |
   | <日期> | T3 | 完成 | |
   ```
2. 在对话中回复：已创建文件清单、`scripts/verify_t1_t3.sh` 的输出、对本文档代码做过的任何修改及原因、写入 `QUESTIONS.md` 的条目。

## 7. 常见陷阱
- `Makefile` 配方行必须用 TAB。
- 使用 `from __future__ import annotations` 时，SQLModel/Pydantic 对前向引用较敏感：若报类型解析错误，先在对应模块末尾调用 `model_rebuild()`，或去掉该 import 并改用显式类型。
- `Session` 在 `models` 与 `sqlmodel` 中同名：`db.py` 已将后者别名为 `DBSession`，不要改回。
- SQLite 在多线程下需要 `check_same_thread=False`（已设置）。
- 不要在测试里读取真实 `.env` 的密钥；测试默认 `LLM_PROVIDER=mock`。
- 完成后**不要**顺手实现 T4/T5；等待下一份任务书。
