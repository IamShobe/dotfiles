#!/usr/bin/env bash
# Resolve this skill's one dependency: the `web-artifacts-builder` skill, with its
# template's node_modules installed and warm.
#
# node_modules is NOT committed (it's ~290MB), so the first run installs it. Every
# later run is a no-op that just prints the path. Idempotent and safe to always call.
#
# Prints the absolute path to the web-artifacts-builder skill on stdout — capture it:
#   WAB="$(bash scripts/ensure-deps.sh)"
#   bash "$WAB/scripts/make-artifact.sh" <name> <App.tsx>
set -euo pipefail

log() { printf '%s\n' "$*" >&2; }   # chatter to stderr; stdout is the path only

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Locate web-artifacts-builder. Sibling in this repo first (the vendored copy that
#    ships alongside this skill), then anywhere the agent may have installed it.
WAB=""
for cand in \
  "$HERE/../../web-artifacts-builder" \
  "$HOME/.claude/skills/web-artifacts-builder" \
  "$HOME/.config/claude/skills/web-artifacts-builder" \
  "$HOME"/.claude/plugins/marketplaces/*/skills/web-artifacts-builder
do
  if [ -f "$cand/scripts/make-artifact.sh" ]; then
    WAB="$(cd "$cand" && pwd)"; break
  fi
done

if [ -z "$WAB" ]; then
  log "❌ web-artifacts-builder not found."
  log "   It ships next to this skill; install the whole repo, not just one skill:"
  log "     npx skills add IamShobe/skills --skill explainer-artifact --skill web-artifacts-builder"
  exit 1
fi

TPL="$WAB/template"
[ -d "$TPL" ] || { log "❌ no template/ in $WAB — the install is incomplete."; exit 1; }

# 2. Ensure node is on PATH (mise/nvm users often have a bare non-login shell).
if ! command -v node >/dev/null 2>&1; then
  if command -v mise >/dev/null 2>&1; then
    PATH="$(dirname "$(mise which node)"):$PATH"; export PATH
  fi
fi
command -v node >/dev/null 2>&1 || { log "❌ node not found on PATH — install Node 18+."; exit 1; }

# 3. Install the template's deps once. vite is the sentinel the build script itself checks.
if [ ! -f "$TPL/node_modules/vite/bin/vite.js" ]; then
  log "→ First run: installing web-artifacts-builder template deps (~290MB, a minute or two)…"
  PM=""
  for c in pnpm npm; do command -v "$c" >/dev/null 2>&1 && { PM="$c"; break; }; done
  # corepack can provide pnpm when it isn't installed standalone
  if [ "$PM" != "pnpm" ] && command -v corepack >/dev/null 2>&1; then
    corepack enable pnpm >/dev/null 2>&1 && command -v pnpm >/dev/null 2>&1 && PM="pnpm"
  fi
  [ -n "$PM" ] || { log "❌ neither pnpm nor npm found — install one."; exit 1; }

  if [ "$PM" = "pnpm" ]; then
    ( cd "$TPL" && pnpm install --frozen-lockfile >&2 ) || {
      log "→ frozen install failed (lockfile drift); retrying unpinned…"
      ( cd "$TPL" && pnpm install >&2 )
    }
  else
    log "⚠️  pnpm not available; falling back to npm (pnpm-lock.yaml is ignored)."
    ( cd "$TPL" && npm install >&2 )
  fi
  log "✅ template deps installed."
fi

[ -f "$TPL/node_modules/vite/bin/vite.js" ] || { log "❌ install finished but vite is missing."; exit 1; }

printf '%s\n' "$WAB"
