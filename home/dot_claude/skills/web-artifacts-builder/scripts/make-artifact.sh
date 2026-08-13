#!/bin/bash
# One-shot: clone the warm template, drop in an App.tsx, and bundle — all in a single call.
# Collapses the clone→edit→build round-trips into one, so the only agent turns are
# "write App.tsx" then "run this". Prints the bundle path ready for the Artifact tool.
#
# Usage:
#   make-artifact.sh <name> <app.tsx-path>   # use an App.tsx you've already written
#   make-artifact.sh <name>                  # App.tsx already sits in <name>/src, just (re)build
#   cat app.tsx | make-artifact.sh <name> -  # read App.tsx from stdin
#
# NAME is created relative to the cwd this script runs in — since shell cwd does
# NOT persist between separate tool calls in most agent harnesses, always run
# `cd <dir> && bash make-artifact.sh ...` as ONE call, not as two calls that
# assume an earlier `cd` stuck. App.tsx's path is resolved to absolute before
# any cd, so that argument alone is safe from cwd drift.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
NAME="${1:?usage: make-artifact.sh <name> [app.tsx-path | -]}"
APP="${2:-}"

# resolve APP to an absolute path *before* any cd, so relative paths survive
# regardless of where NAME ends up being created
if [ -n "$APP" ] && [ "$APP" != "-" ]; then
  [ -f "$APP" ] || { echo "❌ app source not found: $APP"; exit 1; }
  APP="$(cd "$(dirname "$APP")" && pwd)/$(basename "$APP")"
fi

# ensure node is on PATH even in a bare shell (mise users)
command -v node >/dev/null 2>&1 || export PATH="$(dirname "$(mise which node)"):$PATH"

# 1. clone (skip if it already exists — lets you re-run to rebuild after an edit).
#    Guard against a stale/incomplete dir (e.g. left over from an interrupted
#    or misdirected run) rather than failing later with a confusing cp error.
if [ -d "$NAME" ] && [ ! -d "$NAME/src" ]; then
  echo "❌ $NAME exists but has no src/ — stale or incomplete directory."
  echo "   Remove it first: rm -rf $NAME"
  exit 1
fi
if [ ! -d "$NAME" ]; then
  bash "$HERE/new-artifact.sh" "$NAME" >/dev/null
fi

# 2. install the App source, if provided
if [ "$APP" = "-" ]; then
  cat > "$NAME/src/App.tsx"
elif [ -n "$APP" ]; then
  [ -f "$APP" ] || { echo "❌ app source not found: $APP"; exit 1; }
  cp "$APP" "$NAME/src/App.tsx"
fi

# 3. set the document <title> — this is what the Artifact gallery/browser tab shows.
#    Priority: `// @title: My Title` on any line of App.tsx  >  the artifact name.
#    Written every run (not just on clone) so editing @title and rebuilding takes effect.
TITLE="$(sed -n 's|^[[:space:]]*//[[:space:]]*@title:[[:space:]]*\(.*\)$|\1|p' "$NAME/src/App.tsx" 2>/dev/null | head -1)"
[ -n "$TITLE" ] || TITLE="$NAME"
node - "$NAME/index.html" "$TITLE" <<'NODE'
const fs = require('fs')
const [file, title] = process.argv.slice(2)
const esc = title.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
const html = fs.readFileSync(file, 'utf8')
const next = html.replace(/<title>[\s\S]*?<\/title>/, `<title>${esc}</title>`)
if (next !== html) fs.writeFileSync(file, next)
NODE

# 4. build
bash "$HERE/build-artifact-fast.sh" "$NAME" >/dev/null

BUNDLE="$NAME/bundle.html"
echo "✅ $BUNDLE ($(du -h "$BUNDLE" | cut -f1)) — publish this path with the Artifact tool"
