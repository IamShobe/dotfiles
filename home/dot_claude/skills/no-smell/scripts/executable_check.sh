#!/usr/bin/env bash
# Smell scan. Each hit is a candidate: fix it, or justify it in one line.
#   check.sh                 files changed on this branch (committed + staged + unstaged + untracked)
#   check.sh <base-ref>      same, against a specific base
#   check.sh -- <files...>   exactly these files
# Exit 0 clean, 1 smells found, 2 usage error.
# Suppress a deliberate hit with a trailing `// no-smell: <reason>` (or `# no-smell: <reason>`).
set -uo pipefail

collect_changed_files() {
  local root base tracked
  root=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "not a git repo" >&2; exit 2; }
  cd "$root" || exit 2
  base=${1:-$(git merge-base HEAD "$(git symbolic-ref -q --short refs/remotes/origin/HEAD || echo origin/main)" 2>/dev/null)}
  if git rev-parse -q --verify HEAD >/dev/null; then
    tracked=$(git diff --name-only --diff-filter=d "${base:-HEAD}")
  else
    tracked=$(git ls-files)
  fi
  { echo "$tracked"; git ls-files --others --exclude-standard; } | sort -u
}

if [[ ${1:-} == "--" ]]; then shift; files=$(printf '%s\n' "$@"); else files=$(collect_changed_files "${1:-}"); fi

ts=(); ts_src=(); py=()
while IFS= read -r f; do
  [[ -f $f ]] || continue
  case $f in
    *.d.ts|*.gen.ts|*/generated/*|*/node_modules/*|*/dist/*|*/vendor/*) ;;
    *.ts|*.tsx|*.mts|*.cts)
      ts+=("$f")
      [[ $f =~ (\.test\.|\.spec\.|/__tests__/|/__integration__/|/test/|/tests/) ]] || ts_src+=("$f") ;;
    *.py) py+=("$f") ;;
  esac
done <<< "$files"

hits=0; reviews=0
TS_NOISE='^[^:]+:[0-9]+:\s*(//|/\*|\*)|no-smell:|binary file matches'
PY_NOISE='^[^:]+:[0-9]+:\s*#|no-smell:|binary file matches'

# scan <smell|review> <noise-filter> <label> <fix> <pattern> <exclude-pattern|-> files...
#   smell  = fails the scan; review = printed for a human look, does not fail
scan() {
  local tier=$1 noise=$2 label=$3 fix=$4 pattern=$5 exclude=$6; shift 6
  (( $# )) || return 0
  local out status
  out=$(rg -n --with-filename --no-heading -e "$pattern" -- "$@"); status=$?
  (( status > 1 )) && { echo "rg failed on rule '$label'" >&2; exit 2; }
  [[ -n $out ]] && out=$(rg -v -e "$noise" <<< "$out")
  [[ $exclude != - && -n $out ]] && out=$(rg -v -e "$exclude" <<< "$out")
  [[ $label == "untyped JSON.parse" && -n $out ]] && out=$(validated_nearby <<< "$out")
  [[ -n $out ]] || return 0
  if [[ $tier == smell ]]; then
    printf '\n== SMELL %s → %s\n%s\n' "$label" "$fix" "$out"; hits=$((hits + 1))
  else
    printf '\n-- review %s → %s\n%s\n' "$label" "$fix" "$out"; reviews=$((reviews + 1))
  fi
}

ID='\b(?:id|\w+(?:Id|ID))\b'
JSON_OK='safeParse|\b[a-z_$][[:word:]$]*\.parse\(|\)\.parse\(|\w*Schema\.parse\(|\.transform\(|:\s*unknown\b|as\s+unknown\b'

# Drop hits whose next 2 lines validate the value (`const raw = JSON.parse(x)` then `schema.safeParse(raw)`).
validated_nearby() {
  local line file n
  while IFS= read -r line; do
    file=${line%%:*}; n=${line#*:}; n=${n%%:*}
    sed -n "$((n + 1)),$((n + 2))p" "$file" | rg -q -e "$JSON_OK" || echo "$line"
  done
}

if (( ${#ts[@]} )); then
  scan smell "$TS_NOISE" "switch"         "match(x).with(...).exhaustive()" \
       '\bswitch\s*\(' - "${ts[@]}"
  scan smell "$TS_NOISE" ".otherwise"     ".exhaustive(), or justify with // no-smell:" \
       '\.otherwise\(' - "${ts[@]}"
  scan smell "$TS_NOISE" "nested ternary" "ts-pattern or a named helper" \
       '\s\?\s[^:?]*\s\?\s[^:]*:|\s\?\s[^:?]*:\s[^,;?}]*\s\?\s' '\?\.|\?\?' "${ts[@]}"
fi

if (( ${#ts_src[@]} )); then
  scan smell "$TS_NOISE" "any / double cast" "real type or z.infer type" \
       '\bas\s+any\b|:\s*any\b|<any>|\bas unknown as\b' - "${ts_src[@]}"
  scan smell "$TS_NOISE" "untyped JSON.parse" "schema.safeParse(...) on the result" \
       'JSON\.parse\(' "$JSON_OK" "${ts_src[@]}"
  scan review "$TS_NOISE" "string-parsed id" "if we own this id format: carry a typed field instead" \
       "$ID\.(?:split|startsWith|endsWith)\(" - "${ts_src[@]}"
  scan smell "$TS_NOISE" "positional params" "single destructured object param" \
       '^\s*(export\s+)?(async\s+)?function\s*\*?\s*\w+\s*(<[^>]*>)?\(\s*\w+\??\s*:[^,()]+,\s*\w+\??\s*:|^\s*(export\s+)?const\s+\w+\s*=\s*(async\s*)?(<[^>]*>)?\(\s*\w+\??\s*:[^,()]+,\s*\w+\??\s*:' - "${ts_src[@]}"
  scan review "$TS_NOISE" "new class"     "plain functions, unless it follows an existing class pattern here" \
       '^\s*(export\s+)?(default\s+)?(abstract\s+)?class\s+\w+' 'extends\s+\w*(Error|Exception)\b' "${ts_src[@]}"
fi

if (( ${#py[@]} )); then
  scan smell "$PY_NOISE" "Any"        "real type / pydantic model" \
       '(:\s*|->\s*|\[\s*|,\s*)Any\b' - "${py[@]}"
  scan smell "$PY_NOISE" "json.loads" "Model.model_validate_json(...)" \
       'json\.loads\(' - "${py[@]}"
  scan smell "$PY_NOISE" "argparse"   "typer" \
       '^\s*(import argparse|from argparse)' - "${py[@]}"
  scan smell "$PY_NOISE" "elif chain" "match + assert_never" \
       '^\s*elif\s+[\w.]+\s*==' - "${py[@]}"
fi

echo
echo "scanned ${#ts[@]} ts + ${#py[@]} py files; smells: $hits; for review: $reviews"
(( hits == 0 ))
