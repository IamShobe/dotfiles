#!/usr/bin/env bash
# Screenshot diagram files (bare <svg> .html) stacked into one PNG, for a visual check.
#   preview.sh out.png a.html b.html …     # renders each at 1000px wide, light theme
set -euo pipefail
OUT="${1:?usage: preview.sh out.png diagram.html…}"; shift
CH="${CHROME:-}"
for c in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" "/Applications/Chromium.app/Contents/MacOS/Chromium" \
         google-chrome google-chrome-stable chromium chromium-browser; do
  [ -n "$CH" ] && break
  if [ -x "$c" ]; then CH="$c"; elif command -v "$c" >/dev/null 2>&1; then CH="$(command -v "$c")"; fi
done
[ -n "$CH" ] || { echo "no Chrome/Chromium found (set CHROME=…)" >&2; exit 1; }

TMP="$(mktemp -d)"; PAGE="$TMP/preview.html"
{ echo '<!doctype html><meta charset=utf-8><body style="margin:0;padding:16px;background:#eceef0;font:12px system-ui">'
  for f in "$@"; do
    echo "<p style=\"margin:8px 0 4px;color:#555\">$(basename "$f")</p><div style=\"width:1000px;background:#fff\">"
    sed -e 's/<svg /<svg style="width:100%;height:auto;display:block" /' "$f"; echo '</div>'
  done; echo '</body>'; } > "$PAGE"
# Height estimate: sum of viewBox heights scaled to 1000px wide.
H="$(python3 - "$@" <<'PY'
import re, sys
h = 32
for f in sys.argv[1:]:
    m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', open(f).read())
    h += 36 + (1000 * float(m.group(2)) / float(m.group(1)) if m else 600)
print(int(h))
PY
)"
rm -f "$OUT"
"$CH" --headless=new --disable-gpu --hide-scrollbars --no-first-run --use-mock-keychain --password-store=basic \
  --window-size=1032,"$H" --virtual-time-budget=1500 --screenshot="$OUT" "file://$PAGE" >/dev/null 2>&1 &
pid=$! t=0 last=-1
while kill -0 "$pid" 2>/dev/null && [ "$t" -lt 300 ]; do
  if [ -s "$OUT" ]; then s="$(wc -c <"$OUT")"; [ "$s" = "$last" ] && break; last="$s"; fi
  sleep 0.1; t=$((t + 1))
done
kill -9 "$pid" 2>/dev/null || true; rm -rf "$TMP"
[ -s "$OUT" ] && echo "📸 $OUT" || { echo "screenshot failed" >&2; exit 1; }
