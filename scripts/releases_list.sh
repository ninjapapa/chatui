#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIR="$ROOT_DIR/dist-releases"

if [[ ! -d "$DIR" ]]; then
  echo "No releases yet (missing dist-releases/)" >&2
  exit 0
fi

ls -1 "$DIR" | sort
