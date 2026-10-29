# 部署说明（sutai）

## 服务器信息（2026-10-25 探测）
| 项目 | 值 |
|---|---|
| 主机 | sutai（10.20.213.110，SSH 端口 22，用户 sutai） |
| 系统 | Ubuntu（内核 6.8.0-137-generic），Python 3.12.3 |
| 硬件 | RTX 4090 D 24GB / 503GB 内存 / 根分区 7.4T 空闲 |
| Node/pnpm | 无（前端在开发机本地构建后随 rsync 上传 dist） |
| sudo | 不可用（`sudo -n true` 失败） |
| 端口 | 8000（应用，0.0.0.0）、11434（Ollama，0.0.0.0） |

## 访问
- 应用：<http://10.20.213.110:8000/>（内网直连，无鉴权）
- 健康：`curl http://10.20.213.110:8000/api/health`

## 目录与连接
- 服务器目录：`~/rep-trainer`
- 连接方式：`ssh sutai`（`~/.ssh/config` 已配置部署专用密钥 `~/.ssh/rep_trainer_sutai`，公钥已加入服务器 authorized_keys；serverctl 仍可正常使用）

## 进程管理
- 应用：`bash scripts/run_prod.sh {start|stop|restart|status}`（nohup + `run/app.pid`，日志 `logs/app.log`）
- 开机自启：`crontab -l` 中两条 `@reboot ... # rep-trainer`（Ollama + 应用）
- Ollama：用户态 `~/bin/ollama serve`（`OLLAMA_HOST=0.0.0.0:11434`，记录于 `~/.ollama_env`；日志 `~/ollama.log`；模型 qwen2.5:14b）
- 服务器 `.env`：`LLM_BASE_URL=http://127.0.0.1:11434/v1`、`LLM_MODEL=qwen2.5:14b`

## 一键部署（开发机执行）
```bash
make deploy            # = bash scripts/push_to_server.sh（rsync + 服务器 deploy.sh）
# 服务器依赖安装较慢时（首次）：
ssh sutai 'cd ~/rep-trainer && PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple bash scripts/deploy.sh'
```
deploy.sh：重建 venv（无 python3-venv 包时自动回退 virtualenv）→ 装依赖 → `seed.py` 重建知识库与数据库 → `run_prod.sh restart` → 本机 healthcheck。

## 日志位置
- 应用：`~/rep-trainer/logs/app.log`、启动日志 `logs/boot.log`
- Ollama：`~/ollama.log`
- LLM 用量：`data/usage/*.jsonl`

## 回滚
- 代码：开发机 `git revert` 后重新 `make deploy`；或 `ssh sutai 'cd ~/rep-trainer && git log'` 不适用（服务器无 .git），保留上一次 rsync 前`cp -a`备份（如需可手工 `ssh sutai 'cp -a ~/rep-trainer ~/rep-trainer.bak'`）
- 数据：`make seed` 可随时从仓库内 data 文件全量重建

## 安全说明
**本应用无登录/鉴权**。当前仅监听内网地址 `0.0.0.0:8000`，供内网演示直连。若需暴露公网：
1. 让 uvicorn 只监听 127.0.0.1（`HOST=127.0.0.1 bash scripts/run_prod.sh restart`），并用 nginx + BasicAuth 反代（模板 `deploy/nginx.conf.example`）；或
2. 直接经 SSH 隧道访问：`ssh -L 8000:127.0.0.1:8000 sutai`。

## 待管理员（需 sudo，本轮未执行）
1. `apt install python3.12-venv`（消除 virtualenv 回退）
2. 可选：安装 `deploy/rep-trainer.service` 为 systemd 服务（替代 run_prod+cron，装后须删除 crontab 中两条 `# rep-trainer` 条目避免双进程抢端口）
3. 可选：nginx 反代 + `/etc/nginx/.htpasswd_rep`（公网暴露时必须）

## 离线依赖（服务器无外网）
服务器无法访问 pypi，`make deploy` 在 pip 阶段会失败。机制：在有网的开发机预先下载依赖包到 `wheelhouse/`，服务器离线安装。

- 开发机（有外网）：`make wheelhouse`（即 `bash scripts/build_wheelhouse.sh`，默认目标 Python 3.12 + x86_64 Linux；不同平台用 `SERVER_PY=3.11` 等环境变量覆盖）。
- `scripts/extract_requirements.py` 从 `pyproject.toml` 提取第三方依赖（含 `rag` 可选组），供 `pip download` 与服务器 `pip install --no-index` 使用。
- `scripts/push_to_server.sh` 的 rsync 不排除 `wheelhouse/`（它被 `.gitignore` 忽略，但需随仓库树传到服务器）。
- 服务器 `deploy.sh` 优先 `pip install --no-index --find-links wheelhouse`；无 `wheelhouse/` 时回退在线安装；都失败则沿用现有依赖并告警。

**只在新增或升级依赖时**需要重跑 `make wheelhouse` 再 `make deploy`；当前没有新增依赖，所以暂时不需要。
