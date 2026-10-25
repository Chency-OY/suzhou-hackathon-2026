# AGENTS.md — 医药代表智能演练助手（信尔美版）

> 每次开工前先读本文件，再读 `SPEC.md` 中与当前任务相关的章节。
> 若任务与 SPEC 冲突，以 SPEC 为准；若 SPEC 有歧义，先在 `docs/QUESTIONS.md` 追加一条提问，再按"最保守假设"继续，不要停下来等。

## 项目一句话
用 AI 合成真实医生拜访情境，让医药代表低成本反复演练；演练后给出**可定位到具体对话句子**的评分与合规复盘，并把高分打法沉淀成团队资产。
演示产品：信达生物 **信尔美®（玛仕度肽注射液）**，主科室：内分泌科（另含心内科、消化肝病科场景）。

## 技术栈（默认，勿擅自更换）
- 后端：Python 3.11 + FastAPI + Pydantic v2 + SQLite（SQLModel）
- 检索：ChromaDB（本地持久化）；embedding 通过 `EmbeddingProvider` 抽象
- LLM：统一走 `backend/app/llm/provider.py` 的 `LLMProvider` 抽象；必须同时提供 `MockLLM`（测试/离线兜底）
- 前端：Vite + React + TypeScript + Tailwind + Recharts
- 包管理：后端 `uv`（或 pip + requirements.txt），前端 `pnpm`

## 目录约定
```
backend/app/{main.py,config.py,models/,llm/,rag/,personas/,sessions/,scoring/,compliance/,playbook/,api/}
backend/tests/
data/{sources/,kb/,personas/,scenarios/,rubric/,calibration/}
prompts/            # 所有 prompt 以文件形式存放并版本化，禁止把长 prompt 写死在代码里
frontend/src/
scripts/
docs/
```

## 工作规则
1. **契约先行**：数据结构只能在 `backend/app/models/` 定义，API 只能按 SPEC 第 6 节实现。要改契约，先改 SPEC，再改代码，并在 PR 描述里写明。
2. **小步提交**：一个任务一个分支一次提交说明，提交信息格式 `[T<编号>] 简述`。
3. **每个模块都要有测试**：至少覆盖主流程；LLM 相关一律用 `MockLLM` 写确定性测试，真实模型只在 `scripts/` 下的手动脚本里调用。
4. **Prompt 即代码**：所有 prompt 放 `prompts/*.md`，文件头写版本号；改动必须同步更新版本号和 `prompts/CHANGELOG.md`。
5. **结构化输出**：所有要求 LLM 返回 JSON 的调用，必须用 Pydantic 校验，失败时重试至多 2 次，仍失败则降级返回安全默认值并记录日志。
6. **不碰真实个人信息**：所有医生画像、对话、患者案例均为合成数据；禁止写入任何真实医生姓名、真实医院内部信息。
7. **医学事实必须有出处**：知识库条目必须带 `source` 与 `verified` 字段；`verified=false` 的条目不得进入评分用的"事实核对"环节，只能用于场景灵感。
8. **合规规则可配置**：合规红线放 `data/rubric/compliance_rules.yaml`，不得硬编码在业务逻辑里。
9. **密钥**：只从环境变量读取（`.env` 不入库），提供 `.env.example`。
10. **完成定义（DoD）**：代码 + 测试通过 + 在 `docs/PROGRESS.md` 追加一行（日期、任务编号、状态、已知问题）。

## 常用命令（初始化后请保持可用）
```
make setup      # 安装依赖
make dev        # 同时启动后端(8000)与前端(5173)
make test       # 后端测试 + 前端类型检查
make seed       # 导入知识库与种子画像
make gen-personas N=40   # 批量合成医生画像（需配置 LLM）
```
