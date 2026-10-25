# 交接补充：机器、账号与权限（TEAMMATE_GUIDE.md 之外的部分）

> 主文档看根目录 `TEAMMATE_GUIDE.md`（项目说明、分工、人工事项、验收方法）。
> 本文件只补它不覆盖的：**你上手需要的环境、账号权限和几台机器的实况**。最后更新：2026-10-25。

## 1. 你需要的三个权限（找 liuqiyue 开）

| 权限 | 怎么开 | 说明 |
|---|---|---|
| GitHub 仓库 | 把 GitHub 用户名发他 → Settings → Collaborators 添加 | 仓库：qiyueliu16-cmd/hackathon-2026 |
| 服务器 SSH | 把你的 `~/.ssh/id_ed25519.pub`（没有就 `ssh-keygen -t ed25519` 生成）发他，他加到 sutai 的 authorized_keys | 主机 `sutai`＝10.20.213.110，用户 `sutai`；参考 `~/.ssh/config` 写一个 Host 条目即可直连 |
| 部署 | 有了 SSH 即可：仓库根目录 `make deploy`（rsync + 服务器端 deploy.sh） | 不要传输任何私钥，各用各的公钥 |

## 2. 机器实况

| 机器 | 上面有什么 |
|---|---|
| 你的电脑（开发机角色） | 无特殊依赖；装 node≥18 + pnpm、python≥3.11 即可 `make setup` |
| **sutai**（10.20.213.110，RTX 4090 24GB / 503GB 内存 / 7.4T 空闲，无 sudo、无 Node） | ① 应用 `~/rep-trainer`（uvicorn 单进程，API+前端静态，`bash scripts/run_prod.sh status` 查看）② Ollama `~/bin/ollama` + qwen2.5:14b（端点 `http://10.20.213.110:11434/v1`，openai 兼容，key 随便填非空如 `ollama`）③ `@reboot` cron 自启（crontab 里两条 `# rep-trainer`） |
| GitHub | main 分支即全部进度；服务器不经 GitHub（rsync 直推），push 只为存档协作 |

`.env`（各机器本地，gitignore 不入库）本机开发直接抄：
```
LLM_PROVIDER=openai_compat
LLM_BASE_URL=http://10.20.213.110:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5:14b
LLM_JSON_MODE=true
LLM_TIMEOUT_S=120
```
服务器上的 `.env`（`~/rep-trainer/.env`）已配好，`LLM_BASE_URL` 是 `http://127.0.0.1:11434/v1`（回环），别改回局域网地址。

## 3. 接手第一天建议动作（1 小时）

1. clone + `make setup && make seed && make test`，全绿说明环境通。
2. 打开 http://10.20.213.110:8000 走一遍 `docs/MANUAL_CLICKTHROUGH.md` 的 8 条勾选。
3. 读 `docs/RETROSPECTIVE.md`（已知短板清单）——尤其 **P0 两条**：label.md 加 `verified: true`（需你确认）、浏览器自测。
4. 下一步开发：`TASKS_T11-T15.md`（对话引擎+演练页，任务书已在根目录），交给 GLM 执行即可。

## 4. 指挥 GLM 的一句话模板

> "读 `TEAMMATE_GUIDE.md` 和 `TASKS_T11-T15.md`，按任务书从 P0 开始逐项执行，每完成一个任务跑 `make lint && make test` 后提交，最后按任务书的汇报章节汇报。"
