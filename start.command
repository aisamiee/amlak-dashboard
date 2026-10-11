#!/bin/zsh
# Double-click to open the auction dashboard (starts the local server if it is not running).
cd "$(dirname "$0")"
PORT=8765
if ! curl -s -m 2 -o /dev/null "http://127.0.0.1:$PORT/api/version"; then
  nohup .venv/bin/python -I scripts/serve.py $PORT > /tmp/amlak-dashboard.log 2>&1 &
  for i in {1..20}; do curl -s -m 1 -o /dev/null "http://127.0.0.1:$PORT/api/version" && break; sleep 0.3; done
fi
open "http://127.0.0.1:$PORT/"
