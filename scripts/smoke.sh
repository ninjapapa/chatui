#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

# Ensure playwright is installed
if [[ ! -d node_modules ]]; then
  echo "node_modules not found; run npm install first" >&2
  exit 1
fi

# Install browser if needed (no sudo)
if [[ ! -d "$HOME/.cache/ms-playwright" ]]; then
  echo "Installing Playwright Chromium..." >&2
  npx playwright install chromium
fi

# Pick a port unlikely to collide.
PORT="8090"

# Start backend serving dist/
cd "$ROOT_DIR/backend"
if [[ ! -d .venv ]]; then
  echo "ERROR: backend/.venv not found. Create it first." >&2
  exit 1
fi
# shellcheck disable=SC1091
source .venv/bin/activate

export FRONTEND_DIST="$ROOT_DIR/dist"
export CHATUI_DB_PATH="$(mktemp -t chatui-smoke-XXXX.sqlite3)"
export CHATUI_TEST_MODE="1"
export OPENAI_API_KEY="test"
export PW_BASE_URL="http://127.0.0.1:${PORT}/"

uvicorn app:app --host 127.0.0.1 --port "$PORT" >/tmp/chatui-smoke-backend.log 2>&1 &
BACK_PID=$!

cleanup() {
  kill "$BACK_PID" >/dev/null 2>&1 || true
  rm -f "$CHATUI_DB_PATH" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# Wait for health
for i in {1..80}; do
  if curl -sf "http://127.0.0.1:${PORT}/api/health" >/dev/null; then
    break
  fi
  sleep 0.1
  if [[ $i -eq 80 ]]; then
    echo "Backend failed to start. Log:" >&2
    cat /tmp/chatui-smoke-backend.log >&2 || true
    exit 1
  fi
done

cd "$ROOT_DIR"

npx playwright test
