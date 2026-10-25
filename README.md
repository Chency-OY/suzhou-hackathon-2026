# 医学沟通训练台

面向医药代表的合成情境演练。用户选择课程和场景，与虚构医生对话，结束后逐句回看自己的表达。当前提供「通用医学沟通」与「信尔美产品资料」两组课程。通用课程不读取产品知识库；产品课程以仓库中的公开资料为基础。

## 当前可用

- 16 个经人工整理的合成场景（通用 12、信尔美 4），支持科室、难度和情境筛选。
- 会话创建、对话、结束、回放；练习记录列表保存在当前浏览器，完整对话保存在服务器 SQLite。
- 复盘展示原句、明确识别到的沟通行为和下一次练习建议。**目前没有可信的自动评分**。
- 场景预筛、人工审核清单和隐藏设定泄露检查。人工审核状态仍为 `pending`，未替带教人员作通过决定。

公网预览首页：<https://chenxi-ouyang.online/rep-trainer/>（无需登录）；点击「进入训练」后使用演示账户登录，训练内容和 API 保留访问限制，凭据不在仓库中。首页和训练页使用[信达生物官网公开 Logo](https://www.innoventbio.com/)作视觉参考，并明确标注为非官方原型。这是 **离线演示模式**：医生由确定性规则模拟，不能用于医学或合规判断。原内网 GPU 服务不可从这台公网服务器访问，切换真实模型需单独配置可达的模型端点并完成内容与评分校准。

## 本地运行

```bash
uv venv .venv
uv pip install --python .venv/bin/python -e '.[dev]'
cd frontend && pnpm install && pnpm build && cd ..
VECTOR_STORE=simple .venv/bin/python scripts/seed.py
VECTOR_STORE=simple .venv/bin/uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

运行测试：`bash scripts/verify_t11_t15.sh`；运行本机冒烟：`.venv/bin/python scripts/e2e_smoke.py --base http://127.0.0.1:8000 --with-session`。

## 内容与资料

- 课程目录：`data/programs.json`；画像与场景：`data/personas/personas.jsonl`、`data/scenarios/scenarios.jsonl`。
- 信尔美资料从[信达生物公开说明书](https://img.innoventbio.com/product/W10030842001.pdf)整理；`data/sources/label.md` 记录录入来源和口径。两份不同适应症的说明书不得混用。
- 所有医生、对话和案例均为合成。请勿输入真实患者或医生的个人信息。

部署步骤、回滚和服务日志见 `docs/DEPLOY.md`；任务与已知限制见 `docs/PROGRESS.md`、`docs/INTEGRATION_ISSUES.md`。协作时先拉取 GitHub 最新提交，检查差异后再合并；服务器只部署已经提交并推送的版本，避免覆盖队友工作。
