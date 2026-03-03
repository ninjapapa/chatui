#!/usr/bin/env bash
set -euo pipefail

# Build the frontend and keep timestamped releases for quick rollback.
# Maintains:
# - dist-releases/<timestamp>/ (immutable builds)
# - dist -> dist-releases/<timestamp> (symlink)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TS="$(date +%Y%m%d-%H%M%S)"
RELEASE_DIR="$ROOT_DIR/dist-releases/$TS"

mkdir -p "$ROOT_DIR/dist-releases"

npm run build

if [[ ! -d "$ROOT_DIR/dist" ]]; then
  echo "ERROR: dist/ not found after build" >&2
  exit 1
fi

mv "$ROOT_DIR/dist" "$RELEASE_DIR"
ln -sfn "$RELEASE_DIR" "$ROOT_DIR/dist"

echo "Release created: $RELEASE_DIR" >&2
