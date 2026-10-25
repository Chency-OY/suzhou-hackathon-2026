#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
MARK="# rep-trainer"
mkdir -p "$REPO/logs"
( crontab -l 2>/dev/null | grep -v "$MARK" || true
  echo "@reboot cd $REPO && bash scripts/ensure_ollama.sh >> logs/boot.log 2>&1 $MARK"
  echo "@reboot sleep 20 && cd $REPO && bash scripts/run_prod.sh start >> logs/boot.log 2>&1 $MARK"
) | crontab -
echo "已安装 @reboot 条目："; crontab -l | grep "$MARK"
systemctl is-active cron >/dev/null 2>&1 || systemctl is-active crond >/dev/null 2>&1 || echo "警告：未检测到 cron 服务在运行，@reboot 可能不生效（需管理员启用）"
