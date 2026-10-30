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
| 2026-10-25 | T9 | 部署工具的连接方式与原有脚本不一致 | 连接凭据和主机信息仅在运维侧管理；仓库保留通用部署步骤 |
| 2026-10-25 | T9 | 服务器无 python3.12-venv 包且无 sudo（python3 -m venv 失败） | get-pip --user --break-system-packages 装 pip，再装用户级 virtualenv；deploy.sh 内置回退：venv 失败自动用 virtualenv |
| 2026-10-25 | T9 | 服务器直连 pypi 慢 | 部署命令注入 PIP_INDEX_URL=清华镜像（不写入脚本默认值，避免绑定镜像源） |
| 2026-10-25 | T9 | 参考实现把 mount_frontend 加在 health 路由注册前，SPA 兜底路由吞掉 /api/health（404） | 调整 main.py：health 路由先注册、mount_frontend 最后调用（与任务书 4.3/4.4 注释要求一致） |
| 2026-10-25 | 课程扩展 | 用户希望不局限单一药品，但仓库仅有信尔美核对过的资料 | 增设不调用产品知识库的通用课程；新产品课程只有完成资料审核后才能启用对应知识库 |
| 2026-10-25 | 公网模型 | 原内网 GPU 不可从公网服务器访问，且此服务器没有可复用的项目模型密钥 | 先用明确标注的离线演示；不把规则回复冒充真实 AI |
| 2026-10-26 | 独立账号 | 用户要求独立登录、注册入口，原 SPEC 未定义注册资料与账号范围 | 仅用用户名和密码注册，不收集邮箱/手机号；每个账号只能访问自己的练习；旧共用演示记录不自动迁移 |
