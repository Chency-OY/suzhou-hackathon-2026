# 项目现状快照（自动生成，勿手改）

- 生成时间：2026-10-27 18:15:15
- 分支：main　最近提交：1654248 Add files via upload
- 冻结文件校验（SPEC.md / AGENTS.md 的哈希前 12 位）：7d976436fc9b 38d4aad9a690 

## 最近 15 次提交
```
1654248 Add files via upload
79d10f4 Add initial content to README.md
3e25870 [docs] teammate guide (filled) + T11-T15 task book + slim handover
d433def [docs] handover notes for teammate
8432235 [T10] retrospective: gaps and follow-ups for 2026-10-25
bada30c [T10] integration checks
0048dcc [T9] deployment
3508a32 [T8] frontend skeleton
98df382 [T5-T6] real generation via local Ollama (sutai): 40 personas, 38 scenarios, STRICT verified
e4e7bb2 [T4-T7] add one-command real generation script
c751b92 [T4-T7] verification script and progress log
321479a [T7] read-only scenarios api
f392516 [T6] scenario generation
33340d2 [T5] persona synthesis
bd07715 [T4] knowledge base
```

## 未提交改动
```
?? docs/STATE.md
```

## 目录树（深度 3）
```
.
./.env.example
./.gitignore
./AGENTS.md
./backend
./backend/app
./backend/app/__init__.py
./backend/app/api
./backend/app/compliance
./backend/app/config.py
./backend/app/db.py
./backend/app/deps.py
./backend/app/llm
./backend/app/main.py
./backend/app/models
./backend/app/personas
./backend/app/playbook
./backend/app/rag
./backend/app/scenarios
./backend/app/scoring
./backend/app/sessions
./backend/app/static.py
./backend/tests
./backend/tests/__init__.py
./backend/tests/factories.py
./backend/tests/test_api_scenarios.py
./backend/tests/test_db.py
./backend/tests/test_facts.py
./backend/tests/test_health.py
./backend/tests/test_llm.py
./backend/tests/test_models.py
./backend/tests/test_personas.py
./backend/tests/test_prompts.py
./backend/tests/test_rag.py
./backend/tests/test_scenarios.py
./backend/tests/test_static.py
./data
./data/calibration
./data/calibration/.gitkeep
./data/kb
./data/kb/.gitkeep
./data/kb/facts.yaml
./data/personas
./data/personas/.gitkeep
./data/personas/personas.jsonl
./data/personas/rejects.jsonl
./data/rubric
./data/rubric/.gitkeep
./data/rubric/name_blacklist.txt
./data/scenarios
./data/scenarios/.gitkeep
./data/scenarios/rejects.jsonl
./data/scenarios/scenarios.jsonl
./data/sources
./data/sources/.gitkeep
./data/sources/facts_upstream.yaml
./data/sources/label.md
./deploy
./deploy/env.server.example
./deploy/nginx.conf.example
./deploy/rep-trainer.service
./docs
./docs/DEPLOY.md
./docs/FACTS_REPORT.md
./docs/HANDOVER.md
./docs/INTEGRATION_ISSUES.md
./docs/MANUAL_CLICKTHROUGH.md
./docs/OLLAMA_PROBE.md
./docs/PERSONA_REPORT.md
./docs/PROGRESS.md
./docs/QUESTIONS.md
./docs/RETROSPECTIVE.md
./docs/REVIEW_SAMPLE.md
./docs/SCENARIO_REPORT.md
./docs/STATE.md
./frontend
./frontend/index.html
./frontend/package.json
./frontend/pnpm-lock.yaml
./frontend/postcss.config.js
./frontend/src
./frontend/src/api.ts
./frontend/src/App.tsx
./frontend/src/components
./frontend/src/hooks.ts
./frontend/src/index.css
./frontend/src/labels.ts
./frontend/src/lib.test.ts
./frontend/src/main.tsx
./frontend/src/pages
./frontend/src/types.ts
./frontend/tailwind.config.js
./frontend/tsconfig.json
./frontend/vite.config.ts
./Makefile
./prompts
./prompts/_example.md
./prompts/CHANGELOG.md
./prompts/persona_gen.md
./prompts/scenario_gen.md
./pyproject.toml
./README.md
./scripts
./scripts/build_facts.py
./scripts/check_facts.py
./scripts/ci.sh
./scripts/deploy.sh
./scripts/e2e_smoke.py
./scripts/ensure_ollama.sh
./scripts/export_review.py
./scripts/gen_personas.py
./scripts/gen_scenarios.py
./scripts/healthcheck.sh
./scripts/install_reboot_cron.sh
./scripts/inventory.sh
./scripts/llm_smoke.py
./scripts/ollama_probe.py
./scripts/push_to_server.sh
./scripts/run_prod.sh
./scripts/run_real_gen.sh
./scripts/seed.py
./scripts/verify_t1_t3.sh
./scripts/verify_t4_t7.sh
./SPEC.md
./TASKS_T1-T3.md
./TASKS_T11-T15.md
./TEAMMATE_GUIDE.md
```

## 代码规模（行数）
```
backend/app          1773 行
backend/tests         540 行
frontend/src          380 行
scripts               876 行
prompts                87 行
```

## Makefile 目标
```
setup dev test lint build-facts seed gen-personas gen-scenarios review web-build deploy healthcheck 
```

## 提示词与版本
```
_example.md                  version: 0.1.0
CHANGELOG.md                 
persona_gen.md               version: 0.1.0
scenario_gen.md              version: 0.1.0
```

## 后端接口
```
backend/app/static.py L19      @app.get("/{full_path:path}", include_in_schema=False)
backend/app/api/scenarios.py L47  @router.get("/scenarios", response_model=list[ScenarioItem])
backend/app/api/scenarios.py L63  @router.get("/scenarios/{scenario_id}", response_model=ScenarioDetail)
backend/app/main.py L14  @app.get("/api/health")
```

## 前端路由
```
11:        <Route index element={<ScenarioListPage />} />
12:        <Route path="scenarios/:id" element={<ScenarioDetailPage />} />
13:        <Route path="session/:id" element={<ComingSoonPage title="演练" />} />
14:        <Route path="report/:id" element={<ComingSoonPage title="复盘报告" />} />
15:        <Route path="progress" element={<ComingSoonPage title="我的成长" />} />
16:        <Route path="team" element={<ComingSoonPage title="团队看板" />} />
17:        <Route path="*" element={<ComingSoonPage title="页面不存在" />} />
```

## 数据概况
```
facts：183 条，已核验 61 条；类别 {'company': 22, 'indication': 3, 'dosing': 24, 'safety': 32, 'efficacy': 82, 'competitor': 4, 'guide': 16}
画像：40 个；科室×难度 {'cardiology/easy': 3, 'cardiology/hard': 3, 'cardiology/normal': 4, 'endocrinology/easy': 6, 'endocrinology/hard': 6, 'endocrinology/normal': 8, 'hepatology/easy': 3, 'hepatology/hard': 3, 'hepatology/normal': 4}
场景：38 个；类型 {'first_visit': 8, 'competitor_compare': 6, 'post_conference': 6, 'time_pressure': 5, 'revisit_after_rejection': 3, 'safety_concern': 5, 'off_label_bait': 5}
      科室 {'endocrinology': 19, 'cardiology': 10, 'hepatology': 9}
审核状态：review.json 不存在或为空
预筛结果： 无
label.md： 有
data/ 下的子目录与文件： ['calibration', 'kb', 'personas', 'rubric', 'scenarios', 'sources']
```

## TODO / FIXME（前 20 条）
```
```

## 疑似密钥文件（只列文件名，不显示内容）
```
（空表示未发现；若列出了 .env，确认它没有被提交）
```

## docs/PROGRESS.md 末 15 行
```
| 2026-10-25 | T1 | 完成 | ruff 0.17 新默认规则需适配（见 QUESTIONS） |
| 2026-10-25 | T2 | 完成 | sqlmodel 0.0.48 要求 tz-aware datetime（见 QUESTIONS） |
| 2026-10-25 | T3 | 完成 | 无 |
| 2026-10-25 | P0 | 完成 | verify_t1_t3 与接口预检全部通过 |
| 2026-10-25 | P1 | 完成 | facts 183 条 / 0 错误 / 16 条 guide 类目告警（见 QUESTIONS） |
| 2026-10-25 | P2 | 完成 | mock 冒烟通过；真实调用待配置密钥 |
| 2026-10-25 | T4 | 完成 | chromadb 1.5.9 集合名适配；facts 由上游事实库抽取（见 QUESTIONS） |
| 2026-10-25 | T5 | 完成 | demo 模式 7 个画像（目标 9，配额缺口 2）；真实生成 ≥30 待密钥 |
| 2026-10-25 | T6 | 完成 | demo 模式 7 个场景 0 拒绝；assign_types 打分修正（见 QUESTIONS）；真实生成待密钥 |
| 2026-10-25 | T7 | 完成 | /api/scenarios 无 hidden_objection/traps 泄露 |
| 2026-10-25 | T5/T6 | 完成 | 真实生成完成：sutai 服务器 Ollama + qwen2.5:14b（RTX 4090）；画像 300 候选→258 有效→40 入选零缺口；场景 38 个（拒 2，均因泄露隐藏异议被自动拦截）；STRICT=1 验收通过（T4-T7 VERIFIED）；用量 151 次调用 / 31.4 万 token / 0 降级 |
| 2026-10-25 | P0 | 完成 | node 22 / pnpm 12 就绪；数据文件均在 git；服务器 Python 3.12、无 Node（走本地构建+上传） |
| 2026-10-25 | T8 | 完成 | 前端骨架：场景列表/详情+筛选，构建 172KB(gzip 56.6KB)，vitest 2 通过 |
| 2026-10-25 | T9 | 完成 | 部署 sutai 单进程（uvicorn 托管 API+SPA）；virtualenv 回退、部署密钥打通 ssh/rsync；healthcheck 全绿；@reboot cron 已装；访问 http://10.20.213.110:8000 |
| 2026-10-25 | T10 | 完成 | e2e_smoke 60/60 PASS（含 7 项敏感字段零泄露）；ollama_probe 7/10·1.8s（失败均为泄露拦截，重试兜底 95%）；待人工点通 MANUAL_CLICKTHROUGH |
```

## docs/QUESTIONS.md 末 12 行
```
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
```

## make lint（末 8 行）
```
. .venv/bin/activate && ruff check backend
/bin/sh: .venv/bin/activate: No such file or directory
make: *** [lint] Error 1
```

## make test（末 20 行）
```
. .venv/bin/activate && pytest -q
/bin/sh: .venv/bin/activate: No such file or directory
make: *** [test] Error 1
```
