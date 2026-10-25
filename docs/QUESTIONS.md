# 待确认问题
| 日期 | 任务 | 问题 | 采用的假设 |
|---|---|---|---|
| 2026-10-25 | T1 | AGENTS.md 说后端包管理用 uv，TASKS 的 Makefile 用 venv+pip | 以 TASKS 任务书为准（venv+pip）；对外接口（make 目标）不变 |
| 2026-10-25 | T1 | 本机 Python 为 3.14.7，AGENTS.md 写"Python 3.11" | pyproject 约束 >=3.11 即满足，采用 3.14.7，测试全绿 |
| 2026-10-25 | T1 | ruff 0.17 默认规则新增 I001/C408/UP017，任务书参考代码不满足 | 风格以 ruff 默认规则为准：import 排序交由 `ruff --fix`；factories 改字典字面量；datetime 用 UTC 别名。接口未变 |
| 2026-10-25 | T2 | sqlmodel 0.0.48 将表模型 datetime 列映射为 UTCDateTime，拒绝 naive datetime | `Record.updated_at` 改用 `datetime.now(UTC)`（tz-aware），列语义不变 |
| 2026-10-25 | T3 | `datetime.utcnow()` 已废弃（计划移除） | `usage.py` 改用 `datetime.now(UTC)`，日志字段与格式不变 |
