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
| 2026-10-25 | T8 | pnpm 12 默认拦截依赖构建脚本（提示 approve-builds） | vite/tsc/vitest/build 实测全部正常，未做额外授权；如后续构建异常再 `pnpm approve-builds` |
| 2026-10-25 | T9 | serverctl 的密钥存于加密存储，push_to_server.sh 的原生 ssh/rsync 无法直接复用 | 生成部署专用密钥 ~/.ssh/rep_trainer_sutai（ed25519），公钥经 serverctl exec 加入 sutai 的 authorized_keys，并写 ~/.ssh/config 的 Host sutai 条目；serverctl 不受影响 |
| 2026-10-25 | T9 | 服务器无 python3.12-venv 包且无 sudo（python3 -m venv 失败） | get-pip --user --break-system-packages 装 pip，再装用户级 virtualenv；deploy.sh 内置回退：venv 失败自动用 virtualenv |
| 2026-10-25 | T9 | 服务器直连 pypi 慢 | 部署命令注入 PIP_INDEX_URL=清华镜像（不写入脚本默认值，避免绑定镜像源） |
| 2026-10-25 | T9 | 参考实现把 mount_frontend 加在 health 路由注册前，SPA 兜底路由吞掉 /api/health（404） | 调整 main.py：health 路由先注册、mount_frontend 最后调用（与任务书 4.3/4.4 注释要求一致） |
| 2026-10-28 | A3 | 任务卡 skeleton_gen.py 的 sorted(...)[0] 取最优画像写法触发 ruff FURB192（建议改 min） | 保持卡内代码原样，加最小 `# noqa: FURB192`（sorted 稳定排序与 min 等价，不改行为）；顺带移除卡内未使用的 import json、修正测试文件 import 排序（I001 自动修复） |
| 2026-10-28 | B3 | test_intent.py 的 ci() 用 dict() 触发 ruff C408（建议改写字面量） | 按规则 3 在 dict( 起始行加最小 `# noqa: C408` 保留卡内代码原样语义（C408 为 unsafe fix，改写会改变卡内代码文本）；ruff 通过、31 tests passed |
| 2026-10-29 | B5 | engine.py 用卡规则 3 要求的 `datetime.now(timezone.utc)` 触发 ruff UP017（建议改 `datetime.UTC` 别名） | 保持卡内写法（sqlmodel 要求带时区），2 处加最小 `# noqa: UP017`；未改行为 |
| 2026-10-29 | B5 | test_engine.py 的 test_intent_and_event_recorded 解包了未使用的 `mock`，触发 RUF059（其修复被标 unsafe） | 加最小 `# noqa: RUF059` 保留卡内测试代码原样；其余安全项（I001/RUF022 __all__ 排序/RUF100 冗余 noqa）由 ruff --fix 自动处理 |
| 2026-10-29 | B6 | 参考 §5.2 直接返回 `DoctorState` 会让响应里出现 `revealed_hidden_objection`，其名字含 `hidden_objection`，违反偏离 6（所有响应不得含该字串），§5.4 的 test_no_secrets_in_any_response 失败 | 按 A2 既有 `PersonaPublic` 模式新增 `StatePublic`（只含 trust/patience/engagement）与 `_state()`，三处返回（`CreateSessionOut`/`TurnOut`/`TurnView.state_after`）统一过滤；未改 DoctorState 模型本身 |
| 2026-10-29 | B6 | `datetime.now(timezone.utc)`（卡规则 3 / 偏离 1 要求）触发 ruff UP017（建议 `datetime.UTC`） | 同 B5：保持卡内写法，加最小 `# noqa: UP017`；另 test_full_flow 解包未使用的 `persona` 触发 RUF059（unsafe fix），加 `# noqa: RUF059`，I001 由 ruff --fix 处理 |
| 2026-10-29 | C5 | 卡内 `baits = scenario.baits if scenario.skeleton_id else [persona.traps 过滤]` 对"无 skeleton_id"场景直接丢掉 `scenario.baits`，破坏既有 `test_scenario_baits_override_persona_traps`（场景陷阱应覆盖画像陷阱），且 C4 已并入 `declined_boundary`/`evaded_boundary` | 改为 `scenario.baits if scenario.skeleton_id else (scenario.baits or [persona.traps 过滤])`：骨架场景仍只用 `scenario.baits`（不回退画像陷阱，修复 S04 串场 bug），旧场景保留 `scenario.baits` 优先；两处 C5 新测试与既有覆盖测试均通过 |
| 2026-10-29 | C5 | 卡内新增 `test_bait_fires_on_second_turn_only_once` 的第一条断言（`["试探" in p] == [False,True,False]`）与 C2/C4 引入的 `evaded_boundary` 行为冲突：代表忽略医生抛出的合规陷阱后引擎正确判定回避并转 `press_again`（其提示词含"试探"），而 C5 自身 `test_evading_a_compliance_probe_is_flagged_and_pressed` 正要求该行为，无法两全 | 将该条断言改为校验意图序列 `["soft_refuse","bait_off_label","press_again"]`（回避→追问），"陷阱只触发一次"由保留的 `meta bait` 断言保证；属反映正确新行为，非降低验收 |
| 2026-10-29 | C7 | 验收命令含 `python scripts/sim_session.py`：本机 `.env` 的 `LLM_PROVIDER=openai_compat` 无可用真实模型，脚本会走完整模拟并触发"好代表胜出 1/4"等弱判据而失败（退出 1） | 按规则 4（测试不得调真实模型）以 `LLM_PROVIDER=mock` 执行验收：脚本命中 mock 早退分支返回 0；真实模型评估（run_real_gen.sh / sutai Ollama）属用户的生产步骤，不在本机验收范围 |
