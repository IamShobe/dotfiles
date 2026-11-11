#!/usr/bin/env bash
# Render diagrams, build and verify an artifact in one call:
#
#   build.sh <name> [App.tsx] [--specs specs.json] [--repo <checkout>] [--no-verify]
#
#   --specs      render these diagram specs into <name>/src/diagrams first
#   --repo       the repo the page links into, for verify.sh's source-link check
#                (defaults to the checkout you run from, if any)
#   App.tsx      omit to rebuild after editing <name>/src/App.tsx
#
# Resolves deps, creates the <name>/ workspace if needed, refreshes the kit at
# src/kit, bundles, copies the result to <name>.html (the path to publish), then
# runs verify.sh. Exit status is verify's. Warm rebuild: about a second.
# A skill layered on top copies its own files into <name>/src before calling this.
set -euo pipefail

NAME="" APP="" SPECS="" REPO="" VERIFY=1
while [ $# -gt 0 ]; do
  case "$1" in
    --specs) SPECS="${2:?--specs needs a file}"; shift 2 ;;
    --repo) REPO="${2:?--repo needs a directory}"; shift 2 ;;
    --no-verify) VERIFY=0; shift ;;
    -*) echo "unknown flag $1" >&2; exit 1 ;;
    *) if [ -z "$NAME" ]; then NAME="$1"; else APP="$1"; fi; shift ;;
  esac
done
: "${NAME:?usage: build.sh <name> [App.tsx] [--specs specs.json] [--repo dir] [--no-verify]}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -z "${WAB:-}" ] || [ -z "${DIAGRAM_DESIGN:-}" ]; then eval "$(bash "$HERE/ensure-deps.sh")"; export WAB DIAGRAM_DESIGN; fi

[ -d "$NAME/src" ] || bash "$WAB/scripts/new-artifact.sh" "$NAME" >/dev/null
if [ -n "$SPECS" ]; then
  python3 "$HERE/diagrams/render.py" "$SPECS" --artifact "$NAME" >/dev/null   # errors/warnings go to stderr
fi
mkdir -p "$NAME/src/kit"
cp "$HERE/../template/src/kit/index.tsx" "$NAME/src/kit/index.tsx"

[ -e "$NAME/node_modules" ] || ln -s "$WAB/template/node_modules" "$NAME/node_modules"   # a moved or copied workspace
if ! out="$(bash "$WAB/scripts/make-artifact.sh" "$NAME" $APP 2>&1)"; then
  printf '%s\n' "$out" | tail -25 >&2; echo "❌ bundle failed" >&2; exit 1
fi
cp "$NAME/bundle.html" "$NAME.html"
echo "✅ $NAME.html ($(du -h "$NAME.html" | cut -f1)) — publish this path"

[ "$VERIFY" = 1 ] || exit 0
exec bash "$HERE/verify.sh" "$NAME" ${REPO:+"$REPO"}
