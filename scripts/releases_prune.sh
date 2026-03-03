#!/usr/bin/env bash
set -euo pipefail

# Keep the newest N releases (default 5) and delete the rest.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KEEP="${1:-5}"
DIR="$ROOT_DIR/dist-releases"

if [[ ! -d "$DIR" ]]; then
  echo "No releases to prune (missing dist-releases/)" >&2
  exit 0
fi

mapfile -t items < <(ls -1 "$DIR" | sort)
count=${#items[@]}

if (( count <= KEEP )); then
  echo "Nothing to prune (count=$count <= keep=$KEEP)" >&2
  exit 0
fi

remove=$((count-KEEP))
for ((i=0; i<remove; i++)); do
  rm -rf "$DIR/${items[$i]}"
  echo "Removed $DIR/${items[$i]}" >&2
done
