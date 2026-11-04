#!/usr/bin/env bash
# PostToolUse hook (Edit|Write|MultiEdit): scan the edited TS/Python file with check.sh and
# feed back only smells this edit introduced — lines already present in HEAD are legacy, not
# the model's doing, and reporting them would bury the signal.
# Never fails the tool call: any internal problem exits 0 silently.
set -uo pipefail

here=$(cd "$(dirname "$0")" && pwd)
file=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty' 2>/dev/null) || exit 0
[[ -n $file && -f $file ]] || exit 0
case $file in *.ts|*.tsx|*.mts|*.cts|*.py) ;; *) exit 0 ;; esac

# Scan by repo-relative path so test-dir detection never sees the checkout's own ancestors.
cd "$(dirname "$file")" || exit 0
root=$(git rev-parse --show-toplevel 2>/dev/null) || root=$PWD
cd "$root" || exit 0
rel=${file#"$root"/}
scan=$(bash "$here/check.sh" -- "$rel" 2>/dev/null); (( $? == 1 )) || exit 0

baseline=$(mktemp); trap 'rm -f "$baseline"' EXIT
git ls-files --error-unmatch -- "$rel" >/dev/null 2>&1 && { git show "HEAD:$rel" > "$baseline" 2>/dev/null || :; }

new_smells=$(awk -v baseline="$baseline" '
  BEGIN { while ((getline l < baseline) > 0) seen[l] = 1 }
  /^== SMELL / { header = substr($0, 10); smell = 1; printed = 0; next }
  /^(-- |$|scanned )/ { smell = 0; next }
  smell {
    content = $0; sub(/^[^:]+:[0-9]+:/, "", content)
    if (content in seen) next
    if (!printed) { print "- " header; printed = 1 }
    line = $0; sub(/^[^:]+:/, "", line); print "    line " line
  }' <<< "$scan")

[[ -n $new_smells ]] || exit 0

reason="no-smell: this edit to $(basename "$file") introduced:
$new_smells
Fix each one now (load the no-smell skill if it isn't loaded), or append \`// no-smell: <reason>\` (\`# no-smell:\` in Python) when it's deliberate."
jq -n --arg reason "$reason" '{decision: "block", reason: $reason}'
