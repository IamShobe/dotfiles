#!/usr/bin/env bash
# Locate web-artifacts-builder (the toolchain this skill writes content for) and
# let it prepare itself (template node packages, diagram-design, theme profile).
#
# Installing it is the package manager's job, not this script's: skillshare (or
# the iamshobe marketplace, whose explainer-artifact plugin depends on it).
#
# Prints shell assignments on stdout — eval them:
#   eval "$(bash scripts/ensure-deps.sh)"   # → $WAB, $DIAGRAM_DESIGN
set -euo pipefail

log() { printf '%s\n' "$*" >&2; }   # chatter to stderr; stdout is eval'd
die() { log "❌ $*"; exit 1; }

SKILL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# find_skill <name> <sentinel file relative to the skill dir>
# Sibling first (same skills dir, any agent), then the usual global locations.
find_skill() {
  local name="$1" sentinel="$2" cc="${CLAUDE_CONFIG_DIR:-$HOME/.claude}" pat c
  # Checked in this order; within one glob, the highest version wins. A Claude
  # Code plugin lives at cache/<marketplace>/<plugin>/<version>/, so a dependency
  # from the same marketplace sits at ../../<name>/<version>/.
  local pats=(
    "$SKILL/../$name"
    "$SKILL/../../$name/*"
    "$SKILL/../../$name/*/skills/$name"
    "$cc/skills/$name"
    "$HOME/.agents/skills/$name"
    "$cc/plugins/cache/*/$name/*"
    "$cc/plugins/cache/*/$name/*/skills/$name"
    "$cc/plugins/marketplaces/*/skills/$name"
  )
  for pat in "${pats[@]}"; do
    while IFS= read -r c; do
      [ -n "$c" ] && [ -f "$c/$sentinel" ] && { (cd "$c" && pwd); return 0; }
    done < <(compgen -G "$pat" | sort -V -r)
  done
  return 1
}

WAB="$(find_skill web-artifacts-builder scripts/build.sh)" \
  || die "web-artifacts-builder is not installed. Install it: skillshare install IamShobe/dotfiles/skills/web-artifacts-builder, or the iamshobe marketplace plugin"
exec bash "$WAB/scripts/ensure-deps.sh"
