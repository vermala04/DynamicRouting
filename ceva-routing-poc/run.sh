#!/usr/bin/env bash
# CEVA Routing POC — local dev runner. Starts backend (FastAPI) on :8000 and
# frontend (Vite) on :5173. Ctrl-C stops both.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# Load .env if present (for MISTRAL_API_KEY etc.)
if [[ -f .env ]]; then
  set -a; source .env; set +a
fi

echo "==> CEVA Dynamic Routing POC"
echo "    Backend  : http://localhost:8000"
echo "    Frontend : http://localhost:5173"
echo

# ---------- Backend ----------
echo "==> Setting up Python venv & deps"
cd "$ROOT/backend"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt

echo "==> Generating synthetic data (if missing)"
python data_generator.py

echo "==> Starting backend"
uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}" &
BACK_PID=$!

# ---------- Frontend ----------
cd "$ROOT/frontend"
echo "==> Installing frontend deps"
if [[ ! -d node_modules ]]; then
  npm install
fi

echo "==> Starting frontend"
npm run dev &
FRONT_PID=$!

cleanup() {
  echo
  echo "==> Stopping…"
  kill "$BACK_PID" "$FRONT_PID" 2>/dev/null || true
  wait || true
}
trap cleanup INT TERM EXIT

wait
