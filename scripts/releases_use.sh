#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REL="${1:-}"

if [[ -z "$REL" ]]; then
  echo "Usage: ./scripts/releases_use.sh <timestamp>" >&2
  echo "See available releases: ./scripts/releases_list.sh" >&2
  exit 2
fi

TARGET="$ROOT_DIR/dist-releases/$REL"
if [[ ! -d "$TARGET" ]]; then
  echo "ERROR: release not found: $TARGET" >&2
  exit 1
fi

ln -sfn "$TARGET" "$ROOT_DIR/dist"

echo "Now using dist -> $TARGET" >&2
