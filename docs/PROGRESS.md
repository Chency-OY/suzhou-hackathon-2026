# 进度记录
| 日期 | 任务 | 状态 | 已知问题 |
|---|---|---|---|
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
| 2026-10-28 | Z0 | 完成 | 环境与基线 |
| 2026-10-28 | A1 | 完成 | 场景素材库加载器 |
| 2026-10-28 | A2 | 完成 | Scenario 模型扩展与对外接口收口 |
