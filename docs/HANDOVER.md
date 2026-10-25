# 交接说明（写给接手的队友）

> 写于 2026-10-25，Day 1（T1–T10）全部完成时。作者：liuqiyue（借 ZCode/GLM 完成），接手人：你。
> 读的顺序：本文件 → `AGENTS.md`（工作规则）→ `SPEC.md`（产品全貌）→ `docs/PROGRESS.md`（做到哪了）。

## 一、现在有什么

| 东西 | 位置 | 状态 |
|---|---|---|
| 代码仓库 | https://github.com/qiyueliu16-cmd/hackathon-2026（main，15 commits） | 全部工作已推 |
| 线上 Demo | http://10.20.213.110:8000 （**内网直连，无鉴权**） | 场景列表/筛选/详情可用，e2e 60/60 PASS |
| 服务器 | sutai（10.20.213.110，用户 sutai），目录 `~/rep-trainer` | 单进程 uvicorn（API+前端静态），`@reboot` cron 自启 |
| 本地大模型 | sutai 上 Ollama（`~/bin/ollama`，qwen2.5:14b，RTX 4090 24GB） | 端点 `http://10.20.213.110:11434/v1`，实测 1.8s/次、生成通过率 95% |
| 数据 | 40 个医生画像 / 38 个场景 / 183 条事实库（61 条已核验） | 由本地模型真实生成，已入库 |

## 二、快速上手（你自己的电脑）

```bash
git clone git@github.com:qiyueliu16-cmd/hackathon-2026.git && cd hackathon-2026
make setup            # venv + 后端依赖（含 chromadb）+ 前端依赖，需 node≥18 + pnpm
cp .env.example .env  # 然后编辑（见下）
make seed             # 建知识库 + 导入画像/场景
make test             # 后端 pytest + 前端 tsc/vitest，应全绿
make dev              # 后端 8000；另开终端 cd frontend && pnpm dev → 5173
```

`.env` 关键项（本机开发连服务器上的本地模型）：
```
LLM_PROVIDER=openai_compat
LLM_BASE_URL=http://10.20.213.110:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5:14b
```

部署更新（改完代码后）：`make deploy`（rsync 到 sutai 并重启，需 SSH 权限，见第五节）。

## 三、必读文档（都在仓库里）

- `SPEC.md`：产品定义、API 契约（第 6 节）、核心逻辑（第 7 节）、五天计划（第 9 节）——**Day 2 做什么看这里**
- `AGENTS.md`：工作规则（测试必写、prompt 即代码、提交格式 `[T编号]` 等）
- `TASKS_T1-T3 / T4-T7 / T8-T10.md`：已完成的任务书，含所有实现细节
- `docs/PROGRESS.md`：逐任务进度；`docs/QUESTIONS.md`：**所有偏离任务书的决策及原因**（接手前建议通读）
- `docs/DEPLOY.md`：服务器、部署、回滚、"待管理员"清单
- `docs/RETROSPECTIVE.md`：**已知短板与改进清单（P0/P1/P2）**，接手后先看这个
- `docs/MANUAL_CLICKTHROUGH.md` / `docs/REVIEW_SAMPLE.md`：等你做的两份人工检查

## 四、你需要知道的关键决策/坑

1. **facts.yaml 是从上游事实库机械抽取生成的**（`scripts/build_facts.py` + `data/sources/facts_upstream.yaml`），不是手写的；改数据前先读 QUESTIONS 里对应条目。
2. **`label.md` 没有 front matter → 说明书 88 个分块在 RAG 里全是 `verified=false`**，`only_verified` 检索会排除说明书。这是 RETROSPECTIVE 的 P0#1：确认后给 `label.md` 头部加 `verified: true` 再 `make seed`。
3. `main.py` 里 `mount_frontend` 必须在**所有** API 路由之后调用，否则 SPA 兜底吞掉 `/api/*`（踩过，已修，别改回去）。
4. 换 LLM 供应商/模型后必须重走冒烟 + 小规模试跑（`--candidates 10`），别直接全量。
5. 服务器没有 sudo、没有 Node：venv 用 virtualenv 回退、前端本地构建后 rsync；pip 慢用清华镜像（`PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple`）。
6. 无云端 LLM key 可用（硅基流动余额不足）；如需更强模型给 `.env` 换端点即可，管线不变。
7. 服务器重启后 Ollama 和应用靠 cron `@reboot` 拉起（crontab 里两条 `# rep-trainer`）。

## 五、给你的访问权限（需要 liuqiyue 操作）

- GitHub：把你加为仓库 collaborator（Settings → Collaborators）。
- 服务器：把你的 SSH 公钥发给他，加到 sutai 的 `~/.ssh/authorized_keys`（或走管理员）。他 Mac 上的 `~/.ssh/rep_trainer_sutai` 是部署专用私钥，**不要传输私钥**，各用各的公钥。

## 六、下一步（Day 2，按 SPEC 第 7.1/9 节）

对话引擎：`sessions/engine.py`（信号判定→状态更新→医生台词→结束判定）、`POST /sessions` 与 `/sessions/{id}/turns`、`prompts/signal_judge.md` + `doctor_reply.md`、前端演练页（聊天+信任度/耐心条）。等下一份任务书（TASKS_Day2）或直接按 SPEC 开工。

## 七、等你的人工事项（累计三件）

1. `docs/REVIEW_SAMPLE.md`：20 条场景抽检勾选
2. `data/kb/facts.yaml`：61/183 条已核验，其余对照说明书/文献改 `verified: true`
3. `label.md` front matter 决策（上面第 2 点）
