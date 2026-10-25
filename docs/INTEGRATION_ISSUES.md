# 联调问题清单（T10）

| 编号 | 现象 | 严重度(高/中/低) | 状态(已修/待修/待管理员) | 备注 |
|---|---|---|---|---|
| I1 | 部署后 `/api/health` 404：参考实现把 SPA 兜底路由注册在 health 之前，吞掉了 API 路径 | 高 | 已修 | main.py 调整注册顺序（health→router→mount_frontend）；e2e 复测 60/60 PASS |
| I2 | 服务器缺 `python3.12-venv` 包且无 sudo，`python3 -m venv` 失败 | 中 | 已修（回退方案） | deploy.sh 自动回退用户级 virtualenv；根治需管理员 `apt install python3.12-venv`（见 DEPLOY.md 待管理员） |
| I3 | 应用无登录/鉴权，当前 `0.0.0.0:8000` 内网直连 | 中 | 待决定 | 仅内网演示可接受；公网暴露前必须启用 nginx BasicAuth 或改监听 127.0.0.1 + SSH 隧道（DEPLOY.md 安全说明） |
| I4 | pnpm 12 拦截依赖构建脚本（approve-builds 提示） | 低 | 观察 | vite/tsc/vitest/build 实测正常 |
| I5 | ollama_probe 单次尝试 7/10，3 次失败均为"泄露隐藏异议"被校验拦截 | 低 | 已兜底 | 生产路径含 3 次纠错重试，全量生成实测 95% 通过；泄露校验保留在链路中（OLLAMA_PROBE.md） |
| I6 | 开机自启依赖 cron `@reboot`（非 systemd），服务器重启后 Ollama/应用自动拉起但无崩溃重启能力 | 低 | 待管理员 | 可选安装 deploy/rep-trainer.service（需 sudo），装后删除 crontab 两条目避免双进程 |
