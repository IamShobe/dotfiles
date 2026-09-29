#!/usr/bin/env bash
# Everything an explainer needs from git, in one call, as compact markdown:
# repo slug + SHA (for permalinks), commit story, files grouped by status,
# changed interface lines, migrations, dependency changes.
#
#   gather-facts.sh [base] [head]    # base defaults to the merge-base with the
#                                    # default branch; head defaults to HEAD
#
# Paste `meta` straight into <Page meta={...}>. Read source files only for what
# this can't show (the *why*, exact line ranges to link).
set -euo pipefail

git rev-parse --git-dir >/dev/null 2>&1 || { echo "not a git repo" >&2; exit 1; }
HEAD_REF="${2:-HEAD}"

if [ -n "${1:-}" ]; then
  BASE="$1"
else
  DEF="$(git symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null || true)"
  for c in "$DEF" origin/main origin/master main master; do
    [ -n "$c" ] && git rev-parse -q --verify "$c^{commit}" >/dev/null && { BASE="$c"; break; }
  done
  : "${BASE:?no base found — pass one: gather-facts.sh <base>}"
fi
MB="$(git merge-base "$BASE" "$HEAD_REF")"
SHA="$(git rev-parse "$HEAD_REF")"
RANGE="$MB..$HEAD_REF"

# owner/repo from any GitHub-style remote (ssh, https, scp form); empty if none.
URL="$(git remote get-url origin 2>/dev/null || true)"
REPO="$(printf '%s' "$URL" | sed -E 's#^(ssh://)?(git@|https?://)?[^/:]+[:/]##; s#\.git$##')"
HOST="$(printf '%s' "$URL" | sed -E 's#^(ssh://)?(git@|https?://)?([^/:]+).*#\3#')"

echo "# Facts: $(git rev-parse --abbrev-ref "$HEAD_REF") vs $BASE"
echo
echo '```ts'
if [ -n "$REPO" ]; then
  echo "meta = { repo: '$REPO', sha: '$SHA'$( [ "$HOST" != github.com ] && echo ", host: '$HOST'" ) }"
else
  echo "meta = { sha: '$SHA' }   // no remote: skip source links"
fi
echo '```'

echo; echo "## Commits ($(git rev-list --count "$RANGE"))"
git log --format='- %s' "$RANGE" | head -40

echo; echo "## Files"
STAT="$(git diff --shortstat "$RANGE")"; echo "${STAT# }"
for s in A:Added D:Deleted R:Renamed M:Modified; do
  k="${s%%:*}"; label="${s#*:}"
  list="$(git diff --name-status -M "$RANGE" | awk -v k="$k" '$1 ~ "^"k { if (k=="R") print "- " $2 " → " $3; else print "- " $2 }')"
  [ -n "$list" ] || continue
  n="$(printf '%s\n' "$list" | wc -l | tr -d ' ')"
  echo; echo "**$label ($n)**"
  printf '%s\n' "$list" | head -25
  [ "$n" -gt 25 ] && echo "- … $((n - 25)) more"
done

# Interface-looking lines: declarations, routes, schema DDL. Tests excluded.
IFACE='^[+-][[:space:]]*(export |public |def |func |fn |class |interface |type |enum |struct |trait |message |service |rpc |CREATE |ALTER |DROP |@(Get|Post|Put|Patch|Delete|app\.|router\.)|(get|post|put|patch|delete)\()'
LINES="$(git diff -U0 "$RANGE" -- . ':(exclude)*test*' ':(exclude)*spec*' ':(exclude)*.lock' ':(exclude)*lock.json' ':(exclude)*lock.yaml' \
  | RE="$IFACE" awk 'BEGIN{re=ENVIRON["RE"]} /^\+\+\+ b\//{f=substr($0,7); next} /^--- /{next} $0 ~ re {print f ": " substr($0,1,160)}' | head -60)"
if [ -n "$LINES" ]; then
  echo; echo "## Interface lines (+ added, − removed)"
  echo '```diff'; printf '%s\n' "$LINES"; echo '```'
fi

MIG="$(git diff --name-only "$RANGE" | grep -iE '(^|/)(migrations?|migrate|alembic|flyway|liquibase|schema)(/|\.)' || true)"
if [ -n "$MIG" ]; then echo; echo "## Migrations / schema"; printf -- '- %s\n' $MIG; fi

DEPS="$(git diff --name-only "$RANGE" | grep -E '(^|/)(package\.json|go\.mod|Cargo\.toml|pyproject\.toml|requirements[^/]*\.txt|Gemfile|pom\.xml|build\.gradle(\.kts)?)$' || true)"
if [ -n "$DEPS" ]; then
  echo; echo "## Dependency changes"
  for f in $DEPS; do
    echo "- \`$f\`"
    git diff -U0 "$RANGE" -- "$f" | grep -E '^[+-][[:space:]]*"?[A-Za-z0-9@/_.-]+"?[[:space:]]*[:=]' | grep -vE '^(\+\+\+|---)' | sed 's/^/    /' | head -12
  done
fi
