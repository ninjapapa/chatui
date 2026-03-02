#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "== chatui regression =="

echo "[1/4] Frontend: TypeScript + build"
cd "$ROOT_DIR"
npm run build

echo "[2/4] Backend: unit tests"
cd "$ROOT_DIR/backend"

if [[ ! -d .venv ]]; then
  echo "ERROR: backend/.venv not found. Create it first:"
  echo "  cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate
python -m unittest -v \
  tests.test_db_init \
  tests.test_changelog \
  tests.test_feedback_list \
  tests.test_pm_loop \
  tests.test_connectivity

echo "[3/4] UI smoke"
cd "$ROOT_DIR"
./scripts/smoke.sh

echo "[4/4] Done"
