#!/usr/bin/env bash
# Build an explainer: web-artifacts-builder's build.sh plus this skill's blocks.
#
#   build.sh <name> [App.tsx] [--specs specs.json] [--repo <checkout>] [--no-verify]
#
# Installs kit/index.tsx at src/explainer (App.tsx imports from '@/explainer'),
# then runs $WAB/scripts/build.sh with the same arguments: render the diagram
# specs, bundle, write <name>.html (the path to publish), verify.
set -euo pipefail

NAME="${1:?usage: build.sh <name> [App.tsx] [--specs specs.json] [--repo dir] [--no-verify]}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -z "${WAB:-}" ] || [ -z "${DIAGRAM_DESIGN:-}" ]; then eval "$(bash "$HERE/ensure-deps.sh")"; export WAB DIAGRAM_DESIGN; fi

[ -d "$NAME/src" ] || bash "$WAB/scripts/new-artifact.sh" "$NAME" >/dev/null
mkdir -p "$NAME/src/explainer"
cp "$HERE/../kit/index.tsx" "$NAME/src/explainer/index.tsx"

VERIFY_SKIP_DIRS=explainer exec bash "$WAB/scripts/build.sh" "$@"
