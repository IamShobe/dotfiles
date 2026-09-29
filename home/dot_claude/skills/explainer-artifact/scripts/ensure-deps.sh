#!/usr/bin/env bash
# Resolve everything explainer-artifact needs, fetching whatever is missing:
#
#   web-artifacts-builder  skill  build toolchain (template node_modules installed here)
#   diagram-design         skill  diagram generator
#   explainer profile      file   ~/.diagram-design/profiles/explainer.md
#
# Installed copies win (any agent's skills dir, Claude Code plugins). A missing
# skill is sparse-cloned into this skill's .deps/ so the skill works no matter
# which installer put it here. Idempotent: later runs only print the paths.
#
# Prints shell assignments on stdout — eval them:
#   eval "$(bash scripts/ensure-deps.sh)"   # → $WAB, $DIAGRAM_DESIGN
set -euo pipefail

log() { printf '%s\n' "$*" >&2; }   # chatter to stderr; stdout is eval'd
die() { log "❌ $*"; exit 1; }

SKILL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPS="$SKILL/.deps"

# Where each dependency comes from when it has to be fetched.
WAB_REPO="https://github.com/IamShobe/dotfiles.git"
WAB_PATH="home/dot_claude/skills/web-artifacts-builder"
DD_REPO="https://github.com/cathrynlavery/diagram-design.git"
DD_PATH="skills/diagram-design"

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
    "$DEPS/$name"
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

# fetch_skill <name> <git url> <path in repo> — shallow sparse clone into .deps/
fetch_skill() {
  local name="$1" url="$2" path="$3" tmp
  command -v git >/dev/null 2>&1 || die "git not found — needed to fetch $name."
  log "→ $name not installed; fetching it from $url …"
  tmp="$(mktemp -d)"
  git clone -q --depth 1 --filter=blob:none --sparse "$url" "$tmp/repo" >&2 \
    || { rm -rf "$tmp"; die "could not clone $url"; }
  git -C "$tmp/repo" sparse-checkout set "$path" >&2
  [ -f "$tmp/repo/$path/SKILL.md" ] || { rm -rf "$tmp"; die "$path/SKILL.md missing in $url"; }
  mkdir -p "$DEPS"
  rm -rf "${DEPS:?}/$name"
  mv "$tmp/repo/$path" "$DEPS/$name"
  rm -rf "$tmp"
  log "✅ $name → $DEPS/$name"
}

resolve() {  # resolve <name> <sentinel> <url> <path>
  find_skill "$1" "$2" || { fetch_skill "$1" "$3" "$4" >&2; find_skill "$1" "$2"; } \
    || die "$1 still missing after fetch."
}

WAB="$(resolve web-artifacts-builder scripts/make-artifact.sh "$WAB_REPO" "$WAB_PATH")"
DIAGRAM_DESIGN="$(resolve diagram-design SKILL.md "$DD_REPO" "$DD_PATH")"

# node on PATH (mise/nvm users often run in a bare non-login shell)
if ! command -v node >/dev/null 2>&1 && command -v mise >/dev/null 2>&1; then
  PATH="$(dirname "$(mise which node)"):$PATH"; export PATH
fi
command -v node >/dev/null 2>&1 || die "node not found on PATH — install Node 18+."
command -v python3 >/dev/null 2>&1 || die "python3 not found — scripts/diagram-to-jsx.sh needs it."

# Template deps, once. vite is the sentinel make-artifact.sh itself checks.
TPL="$WAB/template"
[ -d "$TPL" ] || die "no template/ in $WAB — incomplete install."
if [ ! -f "$TPL/node_modules/vite/bin/vite.js" ]; then
  log "→ First run: installing web-artifacts-builder template deps (~290MB, usually <1 min)…"
  PM=""
  for c in pnpm npm; do command -v "$c" >/dev/null 2>&1 && { PM="$c"; break; }; done
  if [ "$PM" != "pnpm" ] && command -v corepack >/dev/null 2>&1; then
    corepack enable pnpm >/dev/null 2>&1 && command -v pnpm >/dev/null 2>&1 && PM="pnpm"
  fi
  [ -n "$PM" ] || die "neither pnpm nor npm found — install one."
  if [ "$PM" = "pnpm" ]; then
    ( cd "$TPL" && pnpm install --frozen-lockfile >&2 ) || {
      log "→ frozen install failed (lockfile drift); retrying unpinned…"
      ( cd "$TPL" && pnpm install >&2 )
    }
  else
    log "⚠️  pnpm not available; falling back to npm (pnpm-lock.yaml is ignored)."
    ( cd "$TPL" && npm install >&2 )
  fi
  [ -f "$TPL/node_modules/vite/bin/vite.js" ] || die "install finished but vite is missing."
  log "✅ template deps installed."
fi

# The explainer diagram profile. Never overwrite one the user already has.
PROFILE="$HOME/.diagram-design/profiles/explainer.md"
if [ ! -f "$PROFILE" ]; then
  mkdir -p "$(dirname "$PROFILE")"
  cp "$SKILL/assets/diagram-design-profile.md" "$PROFILE"
  log "✅ installed diagram-design profile → $PROFILE"
fi

printf 'WAB=%q\nDIAGRAM_DESIGN=%q\n' "$WAB" "$DIAGRAM_DESIGN"
