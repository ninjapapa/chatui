#!/usr/bin/env bash
set -euo pipefail

# Installs a user crontab entry to run the PM loop nightly.
# Default schedule: 02:10 local time.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCHEDULE="${1:-"10 2 * * *"}"

JOB_CMD="cd $ROOT_DIR && $ROOT_DIR/scripts/pm_loop_run.sh >> $ROOT_DIR/backend/data/pm_loop.log 2>&1"
JOB_LINE="$SCHEDULE $JOB_CMD"

mkdir -p "$ROOT_DIR/backend/data"

# Get current crontab (if any)
TMP="$(mktemp)"
crontab -l 2>/dev/null >"$TMP" || true

# If already present, do nothing.
if grep -Fq "$ROOT_DIR/scripts/pm_loop_run.sh" "$TMP"; then
  echo "Cron already contains a pm_loop_run.sh entry. No changes made." >&2
  rm -f "$TMP"
  exit 0
fi

{
  cat "$TMP"
  echo ""
  echo "# chatui: nightly PM loop (skip if no new feedback)"
  echo "$JOB_LINE"
} | crontab -

rm -f "$TMP"

echo "Installed cron entry:" >&2
echo "$JOB_LINE" >&2
