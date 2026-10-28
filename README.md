# 医药代表智能演练助手（Rep Trainer）

一个用于**医药代表拜访演练**的对话训练工具：系统扮演一位虚构医生，代表在真实感场景里练"怎么开口、怎么回应顾虑、怎么合规地推进下一步"。

设计上坚持两条原则：

1. **学术推广优先**：反馈围绕是否切中医生关注点、是否引用可核验证据、是否提出具体下一步，而不是"话术是否说动对方"。
2. **合规优先**：对超适应症宣传、贬低竞品、夸大表述、利益输送与统方等风险行为会给出明确信号提示；合规红线场景会在场景中标注。

> 本项目是**训练工具**，不提供任何医疗建议，也不用于真实的推广沟通。

---

## 本地运行

前置：Python 3.11+（建议用 `make setup` 自动建虚拟环境）、Node 18+ 与 pnpm（前端）。

```bash
make setup                 # 建 .venv 并安装后端依赖；同时安装前端依赖
make seed                  # 从仓库内 data/ 重建知识库与数据库（人物、场景、事实）
make dev                   # 后端 uvicorn 热重载，默认 http://127.0.0.1:8000
cd frontend && pnpm dev    # 前端开发服务器，默认 http://localhost:5173
```

其它常用目标：

| 命令 | 作用 |
|---|---|
| `make test` | 后端 pytest + 前端 tsc/vitest |
| `make lint` | `ruff check backend` |
| `make build-facts` | 从 `data/sources/` 构建事实库 |
| `make gen-personas` / `make gen-scenarios-v2` | 生成人物画像与（骨架驱动的）场景，需要可用的模型服务 |
| `make review` / `make apply-review` | 导出人工审核样本 / 应用审核结果并重新入库 |
| `make sim` | 用脚本化的"好/差代表"跑样例对话，输出到 `docs/SAMPLE_SESSIONS.md` |
| `make web-build` | 构建前端静态资源到 `frontend/dist` |

模型服务通过环境变量配置（`.env`，不入库，参考 `.env.example`）：`LLM_PROVIDER`、`LLM_BASE_URL`、`LLM_MODEL`、`LLM_API_KEY`。
`LLM_PROVIDER=mock` 时不联网，全部走兜底台词，可用于断网演示。

---

## 数据说明

- **全部为合成数据**：人物画像、场景、对话语料均由程序生成，不对应任何真实医生、医院或患者。
- **医学事实**来自公开资料，并在事实库中标注核验状态（`verified`）。核验状态只能由人工确认，代码不会自动改写事实表述。
- **合规规则与评分相关配置**（`data/rubric/`）为**示意版本**，用于训练反馈，不构成合规意见或法律依据。
- 任何台词、提示词与文档中都**不得出现疗效或安全性的具体数字**。

---

## 目录说明

```
backend/      FastAPI 后端
  app/api/        HTTP 接口（场景、会话）
  app/sessions/   对话引擎：状态机、意图选择、规则
  app/personas/   医生画像生成与校验
  app/scenarios/  场景生成、骨架生成、人工审核
  app/corpus/     台词素材库加载
  app/llm/        模型 provider、提示词、结构化输出
  app/rag/        事实检索（知识库）
  app/models/     领域模型与常量
frontend/     React + Vite 前端（场景列表、场景详情、演练页）
prompts/      提示词模板（带版本号，变更记在 prompts/CHANGELOG.md）
data/         数据：画像、场景、事实源、素材库、规则（运行时产物 app.db/chroma/usage 不入库）
scripts/      生成、导入、部署、冒烟脚本
docs/         进度、报告、部署与核验记录
tasks/        任务卡与执行规则
deploy/       部署相关模板
```

接口约定：`GET /api/scenarios`、`GET /api/scenarios/{id}`、`POST /api/sessions`（可带 `pre_goal`）、
`POST /api/sessions/{id}/turns`、`POST /api/sessions/{id}/finish`、`POST /api/sessions/{id}/record`、`GET /api/sessions/{id}`。
对外响应**不包含**内部字段（如 `meta`、`baits`、`turn_plan`、`gold_moves`、`compliance_checks`、`hidden_objection`）。

---

## 免责声明

本工具用于沟通技能训练与教学演示。它不提供医疗、诊断或治疗建议，也不得用于任何真实的药品推广、学术交流或商业沟通场景。
所有的"医生"角色、病例描述与对话内容均为虚构合成，任何与实际医疗决策的关联都应避免。
