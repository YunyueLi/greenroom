#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-"$ROOT/dist/pages"}"

rm -rf "$OUT"
mkdir -p "$OUT/app" "$OUT/brand"

copy_file() {
  local src="$1"
  local dst="${2:-$1}"
  if [ ! -f "$ROOT/$src" ]; then
    echo "missing required deploy asset: $src" >&2
    exit 1
  fi
  mkdir -p "$(dirname "$OUT/$dst")"
  cp "$ROOT/$src" "$OUT/$dst"
}

copy_file index.html
copy_file 404.html
copy_file _headers
copy_file _redirects
copy_file site.webmanifest
copy_file icon.svg
copy_file favicon-32.png
copy_file apple-touch-icon.png
copy_file icon-192.png
copy_file icon-512.png
copy_file og.png
copy_file app/greenroom.html
copy_file app/srs.js
copy_file brand/icon-square.svg
copy_file brand/wordmark-ai.png

find "$OUT" -type f | sort
