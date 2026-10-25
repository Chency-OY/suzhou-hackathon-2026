#!/usr/bin/env bash
# 若 11434 已可用则什么都不做；否则按已有配置启动。环境变量写在 ~/.ollama_env（由 GLM 根据现有进程生成，勿提交）。
if curl -fs --max-time 3 http://127.0.0.1:11434/api/tags >/dev/null; then echo "ollama up"; exit 0; fi
command -v ollama >/dev/null || { echo "ollama not installed"; exit 1; }
[ -f "$HOME/.ollama_env" ] && set -a && . "$HOME/.ollama_env" && set +a
nohup ollama serve >> "$HOME/ollama.log" 2>&1 &
sleep 4
if curl -fs --max-time 3 http://127.0.0.1:11434/api/tags >/dev/null; then echo "ollama started"; else echo "ollama failed"; tail -n 20 "$HOME/ollama.log"; exit 1; fi
