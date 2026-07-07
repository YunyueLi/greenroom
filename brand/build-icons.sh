#!/usr/bin/env bash
# Regenerate the raster icon set from the SVG sources using headless Chrome.
# Sources: icon.svg (squircle, root) · brand/icon-square.svg (full-bleed, maskable) · brand/og.html
# Outputs (repo root): favicon-32.png · apple-touch-icon.png · icon-192.png · icon-512.png · og.png
set -euo pipefail
cd "$(dirname "$0")/.."                       # repo root
ROOT="$PWD"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

shot_svg() {                                  # size  src.svg  out.png  (transparent bg)
  local size="$1" src="$2" out="$3"
  cat > "$TMP/w.html" <<HTML
<!doctype html><meta charset=utf-8>
<style>html,body{margin:0;padding:0}img{display:block;width:${size}px;height:${size}px}</style>
<img src="file://$ROOT/$src">
HTML
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
    --default-background-color=00000000 --window-size="${size},${size}" \
    --screenshot="$ROOT/$out" "file://$TMP/w.html" >/dev/null 2>&1
  echo "  $out  (${size}x${size})"
}

echo "icons:"
shot_svg 32  icon.svg               favicon-32.png
shot_svg 180 brand/icon-square.svg  apple-touch-icon.png
shot_svg 192 brand/icon-square.svg  icon-192.png
shot_svg 512 brand/icon-square.svg  icon-512.png

echo "og:"
"$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
  --window-size=1200,630 --virtual-time-budget=1500 \
  --screenshot="$ROOT/og.png" "file://$ROOT/brand/og.html" >/dev/null 2>&1
echo "  og.png  (1200x630)"
echo "done."
