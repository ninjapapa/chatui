#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Defaults
: "${PM_LOOP_AGENT_ID:=chatui-pm}"
: "${PM_LOOP_REPO:=ninjapapa/chatui}"
if [[ -z "${PM_LOOP_TEST_CMD:-}" ]]; then
  if command -v npm >/dev/null 2>&1; then
    PM_LOOP_TEST_CMD="PATH=$(dirname $(command -v npm)):$PATH $(command -v npm) test"
  else
    PM_LOOP_TEST_CMD="npm test"
  fi
fi
: "${PM_LOOP_APPLY:=1}" # 1 = triage then apply first created issue (if any)

cd "$ROOT_DIR/backend"

if [[ ! -d .venv ]]; then
  echo "ERROR: backend/.venv not found. Create it first:" >&2
  echo "  cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt" >&2
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

export PM_AGENT_ID="$PM_LOOP_AGENT_ID"
export GITHUB_REPO="$PM_LOOP_REPO"
export PM_TEST_CMD="$PM_LOOP_TEST_CMD"

# 1) Triage: analyze feedback + create issues (skips if none)
python pm_loop_gh.py --mode triage

if [[ "$PM_LOOP_APPLY" != "1" ]]; then
  echo "PM_LOOP_APPLY!=1; skipping apply step." >&2
  exit 0
fi

# 2) Apply: pick the first created issue from the latest daily plan and implement it.
PLAN_DIR="$ROOT_DIR/docs/daily"
LATEST_PLAN=""
if [[ -d "$PLAN_DIR" ]]; then
  # newest by mtime
  LATEST_PLAN="$(ls -t "$PLAN_DIR"/*-plan.md 2>/dev/null | head -n 1 || true)"
fi

if [[ -z "$LATEST_PLAN" ]]; then
  echo "No daily plan found; nothing to apply." >&2
  exit 0
fi

# Extract GitHub issue URLs (if any) from the plan.
# Example line: - https://github.com/ninjapapa/chatui/issues/123
ISSUE_URL="$(grep -Eo 'https://github.com/[^ ]+/issues/[0-9]+' "$LATEST_PLAN" | head -n 1 || true)"

if [[ -z "$ISSUE_URL" ]]; then
  echo "No created issue URL found in $LATEST_PLAN; nothing to apply." >&2
  exit 0
fi

echo "Applying issue: $ISSUE_URL" >&2

echo "Using test command: $PM_LOOP_TEST_CMD" >&2

cd "$ROOT_DIR/backend"
python pm_loop_gh.py --mode apply --issue "$ISSUE_URL" --test-cmd "$PM_LOOP_TEST_CMD"
