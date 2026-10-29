# 项目现状快照（自动生成，勿手改）

- 生成时间：2026-10-29 07:48:21
- 分支：main　最近提交：553c502 [B10] 部署、端到端与 README
- 冻结文件校验（SPEC.md / AGENTS.md 的哈希前 12 位）：7d976436fc9b 38d4aad9a690 

## 最近 15 次提交
```
553c502 [B10] 部署、端到端与 README
b921155 [B9] 冒烟：脚本化好/差代表
af91a13 [B8] 前端：开始前写目标、演练页、拜访后写记录
bb19643 [B7] 前端：类型、标签、接口封装
2ca1e3f [B6] 会话接口（含访前目标与拜访记录）
a7d3557 [B5] 对话引擎主体
6509c96 [B4] 提示词 v0.2
87d36d9 [B3] 医生意图选择器
d7f6ac9 [B3] 医生意图选择器
c3bf426 [B2] 场景审核状态机制
2f12542 [B2] 场景审核状态机制
2a35911 [B1] 模型扩展与医生状态机
044ec3b [B1] 模型扩展与医生状态机
e49c381 [A4] 用骨架重新生成场景并入库
f83ea72 [A4] 用骨架重新生成场景并入库
```

## 未提交改动
```
 M docs/STATE.md
```

## 目录树（深度 3）
```
.
./.env
./.env.example
./.gitignore
./AGENTS.md
./Makefile
./MakefileViXsHZ
./README.md
./SPEC.md
./TASKS_T1-T3.md
./TASKS_T11-T15.md
./TASK_CARDS_v1.md
./TEAMMATE_GUIDE.md
./backend
./backend/app
./backend/app/__init__.py
./backend/app/api
./backend/app/compliance
./backend/app/config.py
./backend/app/corpus
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
./backend/rep_trainer.egg-info
./backend/rep_trainer.egg-info/PKG-INFO
./backend/rep_trainer.egg-info/SOURCES.txt
./backend/rep_trainer.egg-info/dependency_links.txt
./backend/rep_trainer.egg-info/requires.txt
./backend/rep_trainer.egg-info/top_level.txt
./backend/tests
./backend/tests/__init__.py
./backend/tests/factories.py
./backend/tests/test_api_scenarios.py
./backend/tests/test_api_sessions.py
./backend/tests/test_corpus.py
./backend/tests/test_db.py
./backend/tests/test_engine.py
./backend/tests/test_facts.py
./backend/tests/test_health.py
./backend/tests/test_intent.py
./backend/tests/test_llm.py
./backend/tests/test_models.py
./backend/tests/test_personas.py
./backend/tests/test_prompt_v2.py
./backend/tests/test_prompts.py
./backend/tests/test_rag.py
./backend/tests/test_review.py
./backend/tests/test_scenario_public.py
./backend/tests/test_scenarios.py
./backend/tests/test_skeleton_gen.py
./backend/tests/test_state.py
./backend/tests/test_static.py
./data
./data/app.db
./data/calibration
./data/calibration/.gitkeep
./data/corpus
./data/corpus/scene_bank_v1.yaml
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
./data/rubric/state_rules.yaml
./data/scenarios
./data/scenarios/.gitkeep
./data/scenarios/rejects.jsonl
./data/scenarios/review.json
./data/scenarios/scenarios.jsonl
./data/scenarios/scenarios_v1.jsonl.bak
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
./docs/SAMPLE_SESSIONS.md
./docs/SCENARIO_REPORT.md
./docs/STATE.md
./frontend
./frontend/.env.development
./frontend/.env.production
./frontend/_tmp_59502_37ac3e38
./frontend/_tmp_59502_37e6de08
./frontend/_tmp_59666_078621d8
./frontend/_tmp_59666_07c0ae20
./frontend/_tmp_59769_0c37b750
./frontend/_tmp_59769_0c4ad5d8
./frontend/index.html
./frontend/package.json
./frontend/pnpm-lock.yaml
./frontend/pnpm-workspace.yaml
./frontend/postcss.config.js
./frontend/src
./frontend/src/App.tsx
./frontend/src/api.ts
./frontend/src/components
./frontend/src/hooks.ts
./frontend/src/index.css
./frontend/src/labels.ts
./frontend/src/lib
./frontend/src/lib.test.ts
./frontend/src/main.tsx
./frontend/src/pages
./frontend/src/types.ts
./frontend/tailwind.config.js
./frontend/tsconfig.json
./frontend/vite.config.ts
./prompts
./prompts/CHANGELOG.md
./prompts/_example.md
./prompts/doctor_reply.md
./prompts/persona_gen.md
./prompts/scenario_fill.md
./prompts/scenario_gen.md
./prompts/signal_judge.md
./pyproject.toml
./scripts
./scripts/apply_review.py
./scripts/build_facts.py
./scripts/check_facts.py
./scripts/ci.sh
./scripts/deploy.sh
./scripts/e2e_smoke.py
./scripts/ensure_ollama.sh
./scripts/export_review.py
./scripts/gen_personas.py
./scripts/gen_scenarios.py
./scripts/gen_scenarios_v2.py
./scripts/healthcheck.sh
./scripts/install_reboot_cron.sh
./scripts/inventory.sh
./scripts/llm_smoke.py
./scripts/ollama_probe.py
./scripts/push_to_server.sh
./scripts/run_prod.sh
./scripts/run_real_gen.sh
./scripts/seed.py
./scripts/sim_session.py
./scripts/taskq.py
./scripts/verify_scenarios_v2.py
./scripts/verify_t1_t3.sh
./scripts/verify_t4_t7.sh
./tasks
./tasks/RULES.md
./tasks/cards
./tasks/cards/01_Z0.md
./tasks/cards/02_A1.md
./tasks/cards/03_A2.md
./tasks/cards/04_A3.md
./tasks/cards/05_A4.md
./tasks/cards/06_B1.md
./tasks/cards/07_B2.md
./tasks/cards/08_B3.md
./tasks/cards/09_B4.md
./tasks/cards/10_B5.md
./tasks/cards/11_B6.md
./tasks/cards/12_B7.md
./tasks/cards/13_B8.md
./tasks/cards/14_B9.md
./tasks/cards/15_B10.md
./tasks/frozen.json
./tasks/status.json
```

## 代码规模（行数）
```
backend/app      2797 行
backend/tests    1148 行
frontend/src     896 行
scripts          1388 行
prompts          203 行
```

## Makefile 目标
```
setup dev test lint build-facts seed gen-personas gen-scenarios gen-scenarios-v2 review web-build deploy healthcheck apply-review sim 
```

## 提示词与版本
```
CHANGELOG.md                 
_example.md                  version: 0.1.0
doctor_reply.md              version: 0.2.0
persona_gen.md               version: 0.1.0
scenario_fill.md             version: 0.1.0
scenario_gen.md              version: 0.1.0
signal_judge.md              version: 0.2.0
```

## 后端接口
```
backend/app/static.py L19      @app.get("/{full_path:path}", include_in_schema=False)
backend/app/api/scenarios.py L64  @router.get("/scenarios", response_model=list[ScenarioItem])
backend/app/api/scenarios.py L80  @router.get("/scenarios/{scenario_id}", response_model=ScenarioDetail)
backend/app/api/sessions.py L108  @router.post("/sessions", response_model=CreateSessionOut)
backend/app/api/sessions.py L122  @router.post("/sessions/{session_id}/turns", response_model=TurnOut)
backend/app/api/sessions.py L135  @router.post("/sessions/{session_id}/finish", response_model=FinishOut)
backend/app/api/sessions.py L150  @router.post("/sessions/{session_id}/record")
backend/app/api/sessions.py L161  @router.get("/sessions/{session_id}", response_model=SessionOut)
backend/app/main.py L16  @app.get("/api/health")
```

## 前端路由
```
12:        <Route index element={<ScenarioListPage />} />
13:        <Route path="scenarios/:id" element={<ScenarioDetailPage />} />
14:        <Route path="session/:id" element={<SessionPage />} />
15:        <Route path="report/:id" element={<ComingSoonPage title="复盘报告" />} />
16:        <Route path="progress" element={<ComingSoonPage title="我的成长" />} />
17:        <Route path="team" element={<ComingSoonPage title="团队看板" />} />
18:        <Route path="*" element={<ComingSoonPage title="页面不存在" />} />
```

## 数据概况
```
facts：183 条，已核验 61 条；类别 {'company': 22, 'indication': 3, 'dosing': 24, 'safety': 32, 'efficacy': 82, 'competitor': 4, 'guide': 16}
画像：40 个；科室×难度 {'cardiology/easy': 3, 'cardiology/hard': 3, 'cardiology/normal': 4, 'endocrinology/easy': 6, 'endocrinology/hard': 6, 'endocrinology/normal': 8, 'hepatology/easy': 3, 'hepatology/hard': 3, 'hepatology/normal': 4}
场景：36 个；类型 {'first_visit': 3, 'second_visit': 3, 'third_visit': 3, 'hard_refusal': 8, 'soft_refusal': 3, 'safety_concern': 3, 'competitor_compare': 2, 'turnover': 2, 'empty_handed': 2, 'compliance_bait': 3, 'off_label_bait': 2, 'followup_visit': 2}
      科室 {'endocrinology': 14, 'cardiology': 13, 'hepatology': 9}
审核状态：{}
预筛结果： 无
label.md： 有
data/ 下的子目录与文件： ['calibration', 'corpus', 'kb', 'personas', 'rubric', 'scenarios', 'sources']
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
| 2026-10-28 | A4 | 完成 | 用骨架重新生成场景并入库 |
| 2026-10-28 | A4 | 完成 | 用骨架重新生成场景并入库 |
| 2026-10-28 | B1 | 完成 | 模型扩展与医生状态机 |
| 2026-10-28 | B1 | 完成 | 模型扩展与医生状态机 |
| 2026-10-28 | B2 | 完成 | 场景审核状态机制 |
| 2026-10-28 | B2 | 完成 | 场景审核状态机制 |
| 2026-10-28 | B3 | 完成 | 医生意图选择器 |
| 2026-10-28 | B3 | 完成 | 医生意图选择器 |
| 2026-10-29 | B4 | 完成 | 提示词 v0.2 |
| 2026-10-29 | B5 | 完成 | 对话引擎主体 |
| 2026-10-29 | B6 | 完成 | 会话接口（含访前目标与拜访记录） |
| 2026-10-29 | B7 | 完成 | 前端：类型、标签、接口封装 |
| 2026-10-29 | B8 | 完成 | 前端：开始前写目标、演练页、拜访后写记录 |
| 2026-10-29 | B9 | 完成 | 冒烟：脚本化好/差代表 |
| 2026-10-29 | B10 | 完成 | 部署、端到端与 README |
```

## docs/QUESTIONS.md 末 12 行
```
| 2026-10-25 | T8 | pnpm 12 默认拦截依赖构建脚本（提示 approve-builds） | vite/tsc/vitest/build 实测全部正常，未做额外授权；如后续构建异常再 `pnpm approve-builds` |
| 2026-10-25 | T9 | serverctl 的密钥存于加密存储，push_to_server.sh 的原生 ssh/rsync 无法直接复用 | 生成部署专用密钥 ~/.ssh/rep_trainer_sutai（ed25519），公钥经 serverctl exec 加入 sutai 的 authorized_keys，并写 ~/.ssh/config 的 Host sutai 条目；serverctl 不受影响 |
| 2026-10-25 | T9 | 服务器无 python3.12-venv 包且无 sudo（python3 -m venv 失败） | get-pip --user --break-system-packages 装 pip，再装用户级 virtualenv；deploy.sh 内置回退：venv 失败自动用 virtualenv |
| 2026-10-25 | T9 | 服务器直连 pypi 慢 | 部署命令注入 PIP_INDEX_URL=清华镜像（不写入脚本默认值，避免绑定镜像源） |
| 2026-10-25 | T9 | 参考实现把 mount_frontend 加在 health 路由注册前，SPA 兜底路由吞掉 /api/health（404） | 调整 main.py：health 路由先注册、mount_frontend 最后调用（与任务书 4.3/4.4 注释要求一致） |
| 2026-10-28 | A3 | 任务卡 skeleton_gen.py 的 sorted(...)[0] 取最优画像写法触发 ruff FURB192（建议改 min） | 保持卡内代码原样，加最小 `# noqa: FURB192`（sorted 稳定排序与 min 等价，不改行为）；顺带移除卡内未使用的 import json、修正测试文件 import 排序（I001 自动修复） |
| 2026-10-28 | B3 | test_intent.py 的 ci() 用 dict() 触发 ruff C408（建议改写字面量） | 按规则 3 在 dict( 起始行加最小 `# noqa: C408` 保留卡内代码原样语义（C408 为 unsafe fix，改写会改变卡内代码文本）；ruff 通过、31 tests passed |
| 2026-10-28 | B3 | test_intent.py 的 ci() 用 dict() 触发 ruff C408（建议改写字面量） | 按规则 3 在 dict( 起始行加最小 `# noqa: C408` 保留卡内代码原样语义（C408 为 unsafe fix，改写会改变卡内代码文本）；ruff 通过、31 tests passed |
| 2026-10-29 | B5 | engine.py 用卡规则 3 要求的 `datetime.now(timezone.utc)` 触发 ruff UP017（建议改 `datetime.UTC` 别名） | 保持卡内写法（sqlmodel 要求带时区），2 处加最小 `# noqa: UP017`；未改行为 |
| 2026-10-29 | B5 | test_engine.py 的 test_intent_and_event_recorded 解包了未使用的 `mock`，触发 RUF059（其修复被标 unsafe） | 加最小 `# noqa: RUF059` 保留卡内测试代码原样；其余安全项（I001/RUF022 __all__ 排序/RUF100 冗余 noqa）由 ruff --fix 自动处理 |
| 2026-10-29 | B6 | 参考 §5.2 直接返回 `DoctorState` 会让响应里出现 `revealed_hidden_objection`，其名字含 `hidden_objection`，违反偏离 6（所有响应不得含该字串），§5.4 的 test_no_secrets_in_any_response 失败 | 按 A2 既有 `PersonaPublic` 模式新增 `StatePublic`（只含 trust/patience/engagement）与 `_state()`，三处返回（`CreateSessionOut`/`TurnOut`/`TurnView.state_after`）统一过滤；未改 DoctorState 模型本身 |
| 2026-10-29 | B6 | `datetime.now(timezone.utc)`（卡规则 3 / 偏离 1 要求）触发 ruff UP017（建议 `datetime.UTC`） | 同 B5：保持卡内写法，加最小 `# noqa: UP017`；另 test_full_flow 解包未使用的 `persona` 触发 RUF059（unsafe fix），加 `# noqa: RUF059`，I001 由 ruff --fix 处理 |
```

## make lint（末 8 行）
```
. .venv/bin/activate && ruff check backend
All checks passed!
```

## make test（末 20 行）
```
. .venv/bin/activate && pytest -q
........................................................................ [ 56%]
........................................................                 [100%]
128 passed in 0.87s

 RUN  v2.1.9 /Users/liuqiyue/hackathon-2026/frontend

 ✓ src/lib.test.ts (4 tests) 3ms

 Test Files  1 passed (1)
      Tests  4 passed (4)
   Start at  07:48:29
   Duration  3.99s (transform 55ms, setup 0ms, collect 101ms, tests 3ms, environment 0ms, prepare 261ms)

```
