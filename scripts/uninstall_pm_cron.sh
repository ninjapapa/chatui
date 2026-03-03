#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

TMP="$(mktemp)"
crontab -l 2>/dev/null >"$TMP" || true

grep -vF "$ROOT_DIR/scripts/pm_loop_run.sh" "$TMP" | crontab -
rm -f "$TMP"

echo "Removed cron entries containing: $ROOT_DIR/scripts/pm_loop_run.sh" >&2
