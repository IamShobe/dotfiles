#!/bin/zsh
# vim: set filetype=zsh:
# `claude` → local LiteLLM gateway (127.0.0.1:4000) → Anthropic (subscription OAuth
# passthrough) or work Azure Foundry models, chosen per request by model name.
# Config: ~/.config/litellm/config.yaml.  Escape hatch: CLAUDE_DIRECT=1 claude …

: ${CLAUDE_LITELLM_PORT:=4000}
: ${CLAUDE_LITELLM_CONFIG:=$HOME/.config/litellm/config.yaml}
: ${CLAUDE_LITELLM_LOG:=$HOME/.cache/litellm/proxy.log}
_CLAUDE_LITELLM_KEY="sk-litellm-local"   # must match general_settings.master_key

_claude_litellm_up() {
  curl -sf -m 1 "http://127.0.0.1:${CLAUDE_LITELLM_PORT}/health/liveliness" >/dev/null 2>&1
}

# Start the gateway detached if it isn't serving. LiteLLM mints Azure tokens via the
# `az` CLI, so it must see `az` on PATH — resolve it here, falling back to the mise install.
_claude_litellm_start() {
  local litellm az_dir
  litellm="$(command -v litellm 2>/dev/null)" || litellm="$HOME/.local/bin/litellm"
  [[ -x "$litellm" ]] || { print -u2 "claude-litellm: litellm not installed (pipx install 'litellm[proxy]')"; return 1; }
  az_dir="$(dirname "$(command -v az 2>/dev/null || ls "$HOME"/.local/share/mise/installs/azure-cli/*/bin/az 2>/dev/null | tail -1)")"
  mkdir -p "${CLAUDE_LITELLM_LOG:h}"
  # config.yaml `include`s a machine-local models file (workplace stuff, not in dotfiles);
  # LiteLLM refuses to start if it's missing, so seed an empty one.
  [[ -f "${CLAUDE_LITELLM_CONFIG:h}/models.local.yaml" ]] || print 'model_list: []' >"${CLAUDE_LITELLM_CONFIG:h}/models.local.yaml"
  PATH="${az_dir}:${PATH}" nohup "$litellm" --config "$CLAUDE_LITELLM_CONFIG" \
    --host 127.0.0.1 --port "$CLAUDE_LITELLM_PORT" >>"$CLAUDE_LITELLM_LOG" 2>&1 &!
  local i
  for i in {1..60}; do _claude_litellm_up && return 0; sleep 0.5; done
  print -u2 "claude-litellm: gateway did not come up — see $CLAUDE_LITELLM_LOG"
  return 1
}

claude() {
  if [[ -n "$CLAUDE_DIRECT" ]]; then command claude "$@"; return; fi
  _claude_litellm_up || _claude_litellm_start || { command claude "$@"; return; }
  ANTHROPIC_BASE_URL="http://127.0.0.1:${CLAUDE_LITELLM_PORT}" \
  ANTHROPIC_CUSTOM_HEADERS="x-litellm-api-key: Bearer ${_CLAUDE_LITELLM_KEY}" \
    command claude "$@"
}

# claude-proxy {status|stop|restart|logs}
claude-proxy() {
  case "$1" in
    status)  _claude_litellm_up && print "up on :${CLAUDE_LITELLM_PORT}" || print "down" ;;
    stop)    lsof -ti "tcp:${CLAUDE_LITELLM_PORT}" | xargs -r kill && print "stopped" ;;
    restart) claude-proxy stop 2>/dev/null; _claude_litellm_start && print "up on :${CLAUDE_LITELLM_PORT}" ;;
    logs)    tail -f "$CLAUDE_LITELLM_LOG" ;;
    *)       print -u2 "usage: claude-proxy {status|stop|restart|logs}"; return 2 ;;
  esac
}
