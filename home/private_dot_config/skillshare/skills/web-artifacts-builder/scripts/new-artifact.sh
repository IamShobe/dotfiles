#!/bin/bash
# Fast path: copy only the SOURCE from the pre-installed template, and symlink node_modules.
# No install, no deep copy of the 230MB pnpm farm → near-instant + can't corrupt symlinks.
set -e
NAME="${1:?usage: new-artifact.sh <dir>}"
TPL="$(cd "$(dirname "$0")/.." && pwd)/template"
[ -d "$TPL/node_modules" ] || { echo "❌ template deps missing — run: (cd \"$TPL\" && pnpm install)"; exit 1; }
[ -e "$NAME" ] && { echo "❌ $NAME already exists"; exit 1; }
mkdir -p "$NAME"
# copy everything EXCEPT the heavy dep dir + build output
( cd "$TPL" && find . -maxdepth 1 -mindepth 1 ! -name node_modules ! -name dist ! -name bundle.html \
    -exec cp -R {} "$(cd "$OLDPWD" && pwd)/$NAME/" \; ) 2>/dev/null || \
  rsync -a --exclude node_modules --exclude dist --exclude bundle.html "$TPL/" "$NAME/"
# share deps via a symlink to the template's warm node_modules (instant, read-mostly)
ln -s "$TPL/node_modules" "$NAME/node_modules"
echo "✅ $NAME ready (node_modules symlinked to warm template). Edit src/App.tsx → build-artifact-fast.sh $NAME"
