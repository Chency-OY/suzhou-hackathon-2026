#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PIDFILE=run/app.pid; LOG=logs/app.log; PORT="${PORT:-8000}"; HOST="${HOST:-0.0.0.0}"
mkdir -p run logs
is_running() { [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; }
case "${1:-}" in
  start)
    if is_running; then echo "already running (pid $(cat "$PIDFILE"))"; exit 0; fi
    . .venv/bin/activate
    nohup uvicorn app.main:app --app-dir backend --host "$HOST" --port "$PORT" >> "$LOG" 2>&1 &
    echo $! > "$PIDFILE"; sleep 2
    if is_running; then echo "started (pid $(cat "$PIDFILE"))"; else echo "failed to start"; tail -n 30 "$LOG"; exit 1; fi ;;
  stop)
    if is_running; then kill "$(cat "$PIDFILE")"; rm -f "$PIDFILE"; echo stopped; else echo "not running"; fi ;;
  restart) "$0" stop; sleep 1; "$0" start ;;
  status)
    if is_running; then echo "running (pid $(cat "$PIDFILE"))"; else echo "not running"; exit 1; fi ;;
  *) echo "usage: $0 {start|stop|restart|status}"; exit 2 ;;
esac
