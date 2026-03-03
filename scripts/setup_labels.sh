#!/usr/bin/env bash
set -euo pipefail

# Create helpful labels for PM loop triage (idempotent).
# Safe to run multiple times.

REPO="${GITHUB_REPO:-ninjapapa/chatui}"

ensure_label() {
  local name="$1" color="$2" desc="$3"
  if gh label list -R "$REPO" --limit 200 | awk -F'\t' '{print $1}' | grep -Fxq "$name"; then
    echo "label exists: $name" >&2
    return 0
  fi
  gh label create "$name" -R "$REPO" -c "$color" -d "$desc" || true
}

ensure_label "feedback" "5319e7" "User feedback / product feedback"
ensure_label "feature" "0e8a16" "Feature request"
