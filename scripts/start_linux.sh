#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
command -v python3 >/dev/null || { echo "Python 3.11+ required"; exit 1; }
command -v node >/dev/null || { echo "Node.js 20+ required"; exit 1; }
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
python -m pip install -q -r requirements.txt
if [ ! -d frontend/node_modules ]; then (cd frontend && npm install --silent); fi
(cd frontend && npm run build --silent)
nohup python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 >/dev/null 2>&1 &
for i in {1..30}; do curl -fsS http://127.0.0.1:8000/api/health >/dev/null 2>&1 && break; sleep 1; done
xdg-open http://127.0.0.1:8000 >/dev/null 2>&1 || true
echo "http://127.0.0.1:8000"
