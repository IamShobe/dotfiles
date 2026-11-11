#!/usr/bin/env bash
# PreToolUse(Bash): route recursive text search to rg. rg skips .gitignore'd
# trees (node_modules, dist), runs in parallel and returns far less noise.
# A command containing "allow-grep" passes.
cmd="$(jq -r '.tool_input.command // empty')"
[ -n "$cmd" ] || exit 0
case "$cmd" in *allow-grep*) exit 0 ;; esac
at_command='(^|[;&|(`]|\$\()[[:space:]]*(rtk[[:space:]]+)?'
recursive_grep='grep[[:space:]]([^|;&]*[[:space:]])?(-[[:alpha:]]*[rR][[:alpha:]]*|--recursive)([[:space:]]|$)'
git_grep='git[[:space:]]+grep([[:space:]]|$)'
if printf '%s\n' "$cmd" | grep -Eq "${at_command}(${recursive_grep}|${git_grep})"; then
  echo "Use rg instead of recursive grep or git grep (rg -n PATTERN [path], -l for files, -g '*.ts' to filter); ast-grep (sg) for code structure. Add '# allow-grep' only when grep itself is required." >&2
  exit 2
fi
