# 任务卡规则（每次开工先读，约 1 分钟）

项目：医药代表智能演练助手。你是接手的编码助手，**每次只做当前这一张任务卡**。

1. **只做当前卡**，不要预做后续卡，不要顺手重构。
2. **不得修改 `SPEC.md`、`AGENTS.md`**（`taskq.py` 会校验；被改了要 `git checkout` 恢复）。
3. **时间一律用 `datetime.now(timezone.utc)`**，不要用 `utcnow()`（sqlmodel 要求带时区，见 `docs/QUESTIONS.md` 的 T2 条目）。参考代码里出现 `utcnow()` 一律替换。ruff 新规则与代码冲突时，用最小的 `# noqa: 规则号`，并在 `docs/QUESTIONS.md` 记一行。
4. **测试不得联网、不得调用真实模型**（用 `MockLLM`）。
5. **不替人做决定**：事实核验（`facts.yaml` 的 `verified`）和场景审核状态（`review.json` 的 approved / rejected / needs_fix）只能由人工决定；不得改写 `facts.yaml` 的 `statement`；不得编造医学事实；任何代码、台词、提示词里**不得出现疗效或安全性的具体数字或百分比**。
6. **密钥不入库**；不要提交 `.env`、`data/app.db`、`data/chroma/`、`data/usage/`。
7. **验收**：完成后运行 `python scripts/taskq.py done <卡号>`，通过才算完成。失败时只看输出的**最后 40 行**排查；同一问题连续 3 次修不好，在 `docs/QUESTIONS.md` 记录（日期｜卡号｜现象｜已尝试）后**停下并报告**，不要跳过验收，也不要改验收命令。
8. **提交与推送**（每张卡完成后）：
   `git add -A && git commit -m "[卡号] 标题" && git pull --rebase origin main && git push origin HEAD:main`
   遇到冲突或推送被拒：**不要强推**，停下并报告。
9. **额度将尽或需要停下**：把当前卡号、完成度、半成品文件、下一步命令、已知问题写进 `docs/HANDOFF.md`，提交并推送，再停。
10. 写代码的方式：**先把卡里给的文件原样写入，再跑测试，再按报错最小化修正**。卡里没写的设计，不要自己发挥。

---
