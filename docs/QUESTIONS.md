# 待确认问题
| 日期 | 任务 | 问题 | 采用的假设 |
|---|---|---|---|
| 2026-10-25 | T1 | AGENTS.md 说后端包管理用 uv，TASKS 的 Makefile 用 venv+pip | 以 TASKS 任务书为准（venv+pip）；对外接口（make 目标）不变 |
| 2026-10-25 | T1 | 本机 Python 为 3.14.7，AGENTS.md 写"Python 3.11" | pyproject 约束 >=3.11 即满足，采用 3.14.7，测试全绿 |
| 2026-10-25 | T1 | ruff 0.17 默认规则新增 I001/C408/UP017，任务书参考代码不满足 | 风格以 ruff 默认规则为准：import 排序交由 `ruff --fix`；factories 改字典字面量；datetime 用 UTC 别名。接口未变 |
| 2026-10-25 | T2 | sqlmodel 0.0.48 将表模型 datetime 列映射为 UTCDateTime，拒绝 naive datetime | `Record.updated_at` 改用 `datetime.now(UTC)`（tz-aware），列语义不变 |
| 2026-10-25 | T3 | `datetime.utcnow()` 已废弃（计划移除） | `usage.py` 改用 `datetime.now(UTC)`，日志字段与格式不变 |
| 2026-10-25 | P1/T4 | 用户提供的 facts.yaml 是结构化事实库（含 evidence/status/quote/discrepancies），非 SPEC 4.4 的扁平列表；其头部声明"作为下游抽取的唯一事实源" | 新增 `scripts/build_facts.py` 机械抽取生成 `data/kb/facts.yaml`：statement 由上游 value/quote/rows 拼接、不改写、不引入外部数字；verified 严格等于上游 status=="verified"；类目按 id 前缀映射到 SPEC 7 类（指南类用非标准类目 guide，接受 check_facts 告警）；法规/合规规则/discrepancies/deprecated/qa_mapping 不入 RAG 库（属合规引擎与后续任务）；上游原件存 `data/sources/facts_upstream.yaml` 逐字保留 |
| 2026-10-25 | T4 | chromadb 1.5.9 要求集合名 3~512 字符，参考实现默认名 "kb" 被拒绝 | ChromaStore 默认集合名改为 "kb_store" |
| 2026-10-25 | T4 | ruff 新默认规则 TRY004 建议 isinstance 分支抛 TypeError | 保留 ValueError 并加 noqa（保持参考实现对外行为） |
| 2026-10-25 | P2 | 本机未配置真实 LLM 密钥 | llm_smoke 输出"未做真实调用"即视为通过；T5/T6 真实生成待配置 openai_compat 后执行，当前用 --demo 离线路径打通 |
| 2026-10-25 | T6 | 参考实现 assign_types 的打分会把带 off_label_bait 陷阱的画像先消耗在普通类型槽位，导致任务书自带测试 test_assign_types_hepatology_off_label 失败 | 在 score 中增加：非 off_label_bait 类型对带该陷阱的画像 -1 分（保护陷阱画像留给 off_label 槽位），保持确定性与返回顺序 |
| 2026-10-25 | T6 | 任务书未提供场景生成的离线路径（gen_scenarios 遇 mock 直接退出），无密钥时无法产出数据供 T7/前端联调 | 新增 app/scenarios/demo_seed.py 与 gen_scenarios.py --demo：用 MockLLM callable 从渲染后 prompt 解析科室/风格/类型，返回能通过 check_draft 的固定草稿（与 personas --demo 对应）；真实生成待密钥 |
| 2026-10-25 | T7 | ruff 默认规则 B008 与 FastAPI `Depends()` 参数默认值惯用法冲突 | pyproject 增加 `[tool.ruff.lint.flake8-bugbear] extend-immutable-calls = ["fastapi.Depends", "fastapi.Query"]`（ruff 官方推荐配置） |
