# 部署与同步

公网预览入口：<https://chenxi-ouyang.online/rep-trainer/>。入口展示静态首页；训练页与 API 使用独立账户保护。对话与沟通信号判断接入 DeepSeek；模拟结果不能作为医学或合规依据。

## 部署准备

在目标机器检出 GitHub 中经过审核的提交，安装 Python 与 pnpm，按 README 的本地运行步骤安装依赖、构建前端并导入种子数据。前端生产构建的 base 路径为 `/rep-trainer/`。应用进程只监听本机回环地址，再由 HTTPS 反向代理暴露该子路径。

`deploy/rep-trainer-public.service` 和 `deploy/nginx-public.conf.example` 是模板，需先填写部署目录、监听端口和密码文件路径。公开首页只提供演示介绍；训练页面、静态构建资源和 `/api/` 仍需访问控制。密码、私钥、真实服务器地址与备份位置均不写入仓库。

## 更新顺序

1. 先拉取 GitHub 最新提交，检查协作者的改动与冲突。
2. 运行 `bash scripts/verify_t11_t15.sh`，确认后端测试、前端测试和构建通过。
3. 推送同一提交，再在服务器构建前端、运行种子脚本、重启应用并验证公开首页、受保护训练页及一轮会话。
4. 保留已有 SQLite 会话数据；更新前另行备份。回滚时恢复上一提交的构建与服务配置。

应用日志通过部署环境的服务管理器查看。具体主机、账号、密钥、配置文件位置和备份路径在私有运维记录中维护。

## 模型配置

运行服务通过仅服务器本地可读的环境文件设置 `LLM_PROVIDER=openai_compat`、`LLM_BASE_URL=https://api.deepseek.com`、`LLM_MODEL=deepseek-flash`、`LLM_THINKING=disabled` 和 `LLM_API_KEY`。密钥不能写入仓库或前端构建。默认仍为 mock，便于本地测试；公网服务单独覆盖配置。按需设置 `DAILY_TOKEN_CAP` 控制每日调用量。模型不可用或达到上限时，对话使用备用模拟回复并在页面提示。
