#!/bin/bash
# Fast bundle: Vite + vite-plugin-singlefile. ~0.5s once deps are warm.
set -e
DIR="${1:-.}"; cd "$DIR"
[ -f node_modules/vite/bin/vite.js ] || { echo "❌ run new-artifact.sh (deps must be present)"; exit 1; }
rm -rf dist
node ./node_modules/vite/bin/vite.js build >/dev/null
cp dist/index.html bundle.html
echo "✅ bundle.html ($(du -h bundle.html | cut -f1)) — self-contained, ready to publish"
