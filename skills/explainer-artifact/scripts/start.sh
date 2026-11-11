#!/usr/bin/env bash
# The first call of an explainer, and the only setup call: resolves the
# toolchain, prints the rules the page must follow and the facts of the change.
#
#   start.sh [base] [head] [-- paths…]     (arguments go to gather-facts.sh)
#
# Prints absolute paths, so later calls need no `eval` in a fresh shell.
set -euo pipefail
S="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
eval "$(bash "$S/scripts/ensure-deps.sh" 2>/dev/null)"

cat <<PATHS
# Paths
S=$S
WAB=$WAB
DIAGRAM_DESIGN=$DIAGRAM_DESIGN
build:   bash $WAB/scripts/build.sh <name> App.tsx --specs specs.json --repo <checkout>
example: python3 $WAB/scripts/diagrams/render.py --example <type>

PATHS
for f in "$S/references/readability.md" "$S/references/formatting.md" \
         "$WAB/references/kit.md" "$WAB/references/diagram-types.md"; do
  printf '\n<!-- %s -->\n' "$f"; cat "$f"
done
printf '\n# Facts\n\n'
exec bash "$S/scripts/gather-facts.sh" "$@"
