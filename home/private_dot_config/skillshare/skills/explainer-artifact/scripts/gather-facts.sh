#!/usr/bin/env bash
# Everything an explainer needs from git, in one call, as compact markdown:
# repo slug + SHA (for permalinks), commit story, files grouped by status,
# changed interface lines, migrations, dependency changes.
#
#   gather-facts.sh [base] [head] [-- paths…]
#     base: defaults to the merge-base with the default branch; head: HEAD
#     paths: limit everything to these paths (a monorepo package, one skill…)
#
# Paste `meta` straight into <Page meta={...}>. Read source files only for what
# this can't show (the *why*, exact line ranges to link).
set -euo pipefail

git rev-parse --git-dir >/dev/null 2>&1 || { echo "not a git repo" >&2; exit 1; }
POS=(); PS=()
while [ $# -gt 0 ]; do
  if [ "$1" = "--" ]; then shift; PS=("$@"); break; fi
  POS+=("$1"); shift
done
[ ${#PS[@]} -gt 0 ] || PS=(.)
HEAD_REF="${POS[1]:-HEAD}"

if [ -n "${POS[0]:-}" ]; then
  BASE="${POS[0]}"
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

echo; echo "## Commits ($(git rev-list --count "$RANGE" -- "${PS[@]}"))"
git log --format='- %s' "$RANGE" -- "${PS[@]}" | head -40

echo; echo "## Files"
STAT="$(git diff --shortstat "$RANGE" -- "${PS[@]}")"; echo "${STAT# }"
for s in A:Added D:Deleted R:Renamed M:Modified; do
  k="${s%%:*}"; label="${s#*:}"
  list="$(git diff --name-status -M "$RANGE" -- "${PS[@]}" | awk -v k="$k" '$1 ~ "^"k { if (k=="R") print "- " $2 " → " $3; else print "- " $2 }')"
  [ -n "$list" ] || continue
  n="$(printf '%s\n' "$list" | wc -l | tr -d ' ')"
  echo; echo "**$label ($n)**"
  printf '%s\n' "$list" | head -25
  [ "$n" -gt 25 ] && echo "- … $((n - 25)) more"
done

# One pass over the diff: interface-looking lines with their line numbers, and the
# changed line ranges per file (new side, at meta.sha) for <Src lines="…">.
IFACE='^[+-][[:space:]]*(export |public |def |func |fn |class |interface |type |enum |struct |trait |message |service |rpc |CREATE |ALTER |DROP |@(Get|Post|Put|Patch|Delete|app\.|router\.)|(get|post|put|patch|delete)\()'
DIFFOUT="$(git diff -U0 "$RANGE" -- "${PS[@]}" ':(exclude)*.lock' ':(exclude)*lock.json' ':(exclude)*lock.yaml' \
  | RE="$IFACE" awk '
    BEGIN { re = ENVIRON["RE"] }
    /^\+\+\+ b\// { f = substr($0, 7); test = (f ~ /(test|spec)/); next }
    /^\+\+\+ \/dev\/null/ { f = ""; next }
    /^--- / { next }
    /^@@/ {
      split($2, o, ","); split($3, n, ","); ol = -o[1]; nl = n[1] + 0
      cnt = (n[2] == "" ? 1 : n[2] + 0)
      if (f != "" && cnt > 0) print "R\t" f "\t" nl "\t" nl + cnt - 1
      next
    }
    /^\+/ { if (f != "" && !test && $0 ~ re) print "I\t" f ":" nl "\t" substr($0, 1, 150); nl++; next }
    /^-/  { if (f != "" && !test && $0 ~ re) print "I\t" f " (was L" ol ")\t" substr($0, 1, 150); ol++; next }
  ')"
LINES="$(printf '%s\n' "$DIFFOUT" | awk -F'\t' '$1=="I" {print $2 ": " $3}' | head -60)"
# Widen each added declaration to its whole block (path:start-end at meta.sha), so
# <Src lines="…"> can be pasted without opening the file.
LINES="$(printf '%s\n' "$LINES" | SHA="$SHA" python3 -c '
import os, re, subprocess, sys
cache = {}
def src(path):
    if path not in cache:
        r = subprocess.run(["git", "show", os.environ["SHA"] + ":" + path], capture_output=True, text=True)
        cache[path] = r.stdout.splitlines() if r.returncode == 0 else None
    return cache[path]
ind = lambda l: len(l) - len(l.lstrip())
CLOSE = ("}", ")", "]", "fi", "done", "esac", "end")
for line in sys.stdin.read().splitlines():
    m = re.match(r"^(.+?):(\d+): \+", line)
    lines = src(m.group(1)) if m else None
    if not lines:
        print(line); continue
    n = int(m.group(2)); i0 = n - 1; base = ind(lines[i0]); end = n
    for k in range(i0 + 1, min(len(lines), i0 + 400)):
        t = lines[k]
        if not t.strip():
            continue
        if ind(t) <= base:
            if t.strip().startswith(CLOSE) and t.rstrip().endswith(("{", "(", "[", ":")):
                end = k + 1; continue          # "}) {" closes a signature, opens the body
            end = k + 1 if t.strip().startswith(CLOSE) else end
            break
        end = k + 1
    print(line.replace(f":{n}: +", f":{n}-{end}: +" if end > n else f":{n}: +", 1))
')"
if [ -n "$LINES" ]; then
  echo; echo "## Interface lines (+ added at path:start-end, − removed)"
  echo '```diff'; printf '%s\n' "$LINES"; echo '```'
fi
RANGES="$(printf '%s\n' "$DIFFOUT" | awk -F'\t' '
  $1 == "R" {
    f = $2; s = $3 + 0; e = $4 + 0
    if (!(f in cnt)) { order[++n] = f; cnt[f] = 0 }
    k = cnt[f]
    if (k > 0 && s <= en[f, k] + 4) { if (e > en[f, k]) en[f, k] = e }   # merge near hunks
    else { k = ++cnt[f]; st[f, k] = s; en[f, k] = e }
  }
  END {
    for (i = 1; i <= n && i <= 30; i++) {
      f = order[i]; line = ""
      for (k = 1; k <= cnt[f] && k <= 6; k++) line = line (k > 1 ? ", " : "") (st[f, k] == en[f, k] ? st[f, k] : st[f, k] "-" en[f, k])
      if (cnt[f] > 6) line = line ", …"
      print "- " f ": " line
    }
  }')"
if [ -n "$RANGES" ]; then
  echo; echo '## Link ranges at meta.sha (use as <Src path="…" lines="…" />)'
  printf '%s\n' "$RANGES"
fi

MIG="$(git diff --name-only "$RANGE" -- "${PS[@]}" | grep -iE '(^|/)(migrations?|migrate|alembic|flyway|liquibase|schema)(/|\.)' || true)"
if [ -n "$MIG" ]; then echo; echo "## Migrations / schema"; printf -- '- %s\n' $MIG; fi

DEPS="$(git diff --name-only "$RANGE" -- "${PS[@]}" | grep -E '(^|/)(package\.json|go\.mod|Cargo\.toml|pyproject\.toml|requirements[^/]*\.txt|Gemfile|pom\.xml|build\.gradle(\.kts)?)$' || true)"
if [ -n "$DEPS" ]; then
  echo; echo "## Dependency changes"
  for f in $DEPS; do
    echo "- \`$f\`"
    git diff -U0 "$RANGE" -- "$f" | grep -E '^[+-][[:space:]]*"?[A-Za-z0-9@/_.-]+"?[[:space:]]*[:=]' | grep -vE '^(\+\+\+|---)' | sed 's/^/    /' | head -12
  done
fi
