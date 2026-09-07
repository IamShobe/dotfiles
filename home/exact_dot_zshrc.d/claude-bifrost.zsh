#!/bin/zsh
# Local Bifrost gateway. Provider configuration and secrets are machine-local.
# CLAUDE_DIRECT=1 bypasses the gateway.
: ${CLAUDE_BIFROST_PORT:=4001}
_claude_bifrost_up() {
  curl -sf -m 1 "http://127.0.0.1:${CLAUDE_BIFROST_PORT}/health" >/dev/null 2>&1
}
_claude_bifrost_start() {
  [[ -x "$HOME/.local/bin/bifrost" && -f "$HOME/.config/bifrost/secrets.env" ]] || return 1
  (
    source "$HOME/.config/bifrost/secrets.env"
    local az_bin="$(command -v az 2>/dev/null)"
    [[ -n "$az_bin" ]] || az_bin="$HOME/.local/share/mise/installs/azure-cli/latest/bin/az"
    export PATH="${az_bin:h}:$PATH"
    mkdir -p "$HOME/.cache/bifrost"
    nohup "$HOME/.local/bin/bifrost" -host 127.0.0.1 -port "$CLAUDE_BIFROST_PORT"       -app-dir "$HOME/.config/bifrost" -log-level warn >>"$HOME/.cache/bifrost/proxy.log" 2>&1 &!
  )
  local i
  for i in {1..60}; do _claude_bifrost_up && return 0; sleep 0.5; done
  print -u2 "Bifrost did not start; see ~/.cache/bifrost/proxy.log"
  return 1
}
claude() {
  if [[ -n "$CLAUDE_DIRECT" ]]; then
    env -u ANTHROPIC_BASE_URL -u ANTHROPIC_CUSTOM_HEADERS claude "$@"
    return
  fi
  _claude_bifrost_up || _claude_bifrost_start || return 1
  # OAuth stays owned by Claude Code; never replace it with a gateway token.
  local headers="${ANTHROPIC_CUSTOM_HEADERS:-}"
  headers="$(printf '%s\n' "$headers" | grep -ivE '^x-litellm-api-key:|^x-bf-direct-key:' )"
  ANTHROPIC_BASE_URL="http://127.0.0.1:${CLAUDE_BIFROST_PORT}/anthropic"   ANTHROPIC_CUSTOM_HEADERS="$headers" command claude "$@"
}
claude-proxy() {
  case "$1" in
    status) _claude_bifrost_up && print "Bifrost up: http://127.0.0.1:${CLAUDE_BIFROST_PORT}" || print "Bifrost down" ;;
    start) _claude_bifrost_up || _claude_bifrost_start ;;
    logs) tail -f "$HOME/.cache/bifrost/proxy.log" ;;
    *) print -u2 "usage: claude-proxy {status|start|logs}"; return 2 ;;
  esac
}
