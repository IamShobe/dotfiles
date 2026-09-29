#!/usr/bin/env bash
# Build an explainer in one call:
#
#   build.sh <name> [App.tsx]     # App.tsx omitted → rebuild after editing <name>/src/App.tsx
#
# Resolves deps, creates the <name>/ workspace if needed, installs the kit at
# src/explainer (so App.tsx imports from '@/explainer'), bundles, and copies the
# result to <name>.html, the path to publish. Warm rebuild: well under a second.
set -euo pipefail

NAME="${1:?usage: build.sh <name> [App.tsx]}"; APP="${2:-}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -z "${WAB:-}" ]; then eval "$(bash "$HERE/ensure-deps.sh")"; fi

[ -d "$NAME/src" ] || bash "$WAB/scripts/new-artifact.sh" "$NAME" >/dev/null
mkdir -p "$NAME/src/explainer"
cp "$HERE/../kit/index.tsx" "$NAME/src/explainer/index.tsx"

bash "$WAB/scripts/make-artifact.sh" "$NAME" $APP >/dev/null
cp "$NAME/bundle.html" "$NAME.html"
echo "✅ $NAME.html ($(du -h "$NAME.html" | cut -f1)) — publish this path; verify: bash $HERE/verify.sh $NAME"
