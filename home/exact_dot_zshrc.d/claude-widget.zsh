#!/bin/zsh
# vim: set filetype=zsh:
# Claude quick-ask ZLE widget.
# Ctrl-X Ctrl-A -> inline mini-prompt -> `claude -p ... --model haiku`,
# with recent WezTerm scrollback prepended as context. Loader shown while running.

# Resolve the wezterm CLI binary (not on PATH inside the GUI app).
_claude_ask_wezterm_bin() {
  local bin
  if [[ -n "$WEZTERM_EXECUTABLE" ]]; then
    bin="${WEZTERM_EXECUTABLE%-gui}"            # strip the -gui suffix
    [[ -x "$bin" ]] && { print -r -- "$bin"; return 0; }
  fi
  bin="/Applications/WezTerm.app/Contents/MacOS/wezterm"
  [[ -x "$bin" ]] && { print -r -- "$bin"; return 0; }
  bin="$(command -v wezterm 2>/dev/null)" && { print -r -- "$bin"; return 0; }
  return 1
}

# Capture last ~50 non-blank lines of the current pane's scrollback.
_claude_ask_context() {
  local wt; wt="$(_claude_ask_wezterm_bin)" || return 1
  [[ -n "$WEZTERM_PANE" ]] || return 1
  "$wt" cli get-text --pane-id "$WEZTERM_PANE" 2>/dev/null \
    | grep -v '^[[:space:]]*$' \
    | grep -v '🤖 ask:' \
    | tail -n 50
}

# Resolve the gitleaks binary (mise install isn't always on PATH).
_claude_ask_gitleaks_bin() {
  local bin
  bin="$(command -v gitleaks 2>/dev/null)" && { print -r -- "$bin"; return 0; }
  # mise fallback: newest installed version
  bin=$(print -l "$HOME/.local/share/mise/installs/gitleaks/"*/gitleaks(N) | sort -V | tail -1)
  [[ -x "$bin" ]] && { print -r -- "$bin"; return 0; }
  return 1
}

# Resolve the glow binary (markdown renderer; mise install isn't always on PATH).
_claude_ask_glow_bin() {
  local bin
  bin="$(command -v glow 2>/dev/null)" && { print -r -- "$bin"; return 0; }
  bin=$(print -l "$HOME/.local/share/mise/installs/glow/"*/**/glow(N.x) | sort -V | tail -1)
  [[ -x "$bin" ]] && { print -r -- "$bin"; return 0; }
  return 1
}

# Render markdown ($1 = text) with glow, styled to the terminal width. Falls back
# to the raw text if glow is missing or errors. CLICOLOR_FORCE=1 keeps styling
# even when stdout isn't detected as a TTY. `command cat` avoids the bat alias.
_claude_ask_render() {
  local text="$1" glow rendered
  glow="$(_claude_ask_glow_bin)" || { print -r -- "$text"; return 0; }
  # Explicit "dark" style + CLICOLOR_FORCE guarantees ANSI styling even when
  # stdout is captured (glow's "auto" disables color when it can't detect a TTY).
  # Terminal theme is tomorrow-night (dark); change to "light" if that flips.
  # -w 0 disables glow's width word-wrap+padding (which left ugly full-width
  # trailing space fill). The awk pass then collapses glow's whitespace-only
  # margin lines to a single blank between blocks and trims leading/trailing
  # blanks — fixing the sprawled, over-indented spacing.
  rendered="$(print -r -- "$text" | CLICOLOR_FORCE=1 "$glow" -s dark -w 0 - 2>/dev/null \
    | awk '
        { line=$0; t=$0; gsub(/\033\[[0-9;]*m/,"",t); gsub(/[ \t]+$/,"",t)
          if (t=="") { blank++; next }
          if (printed && blank>0) print ""
          blank=0; printed=1; print line
        }')"
  if [[ -n "$rendered" ]]; then
    print -r -- "$rendered"
  else
    print -r -- "$text"   # glow failed → show raw rather than nothing
  fi
}

# Redact secrets from text (stdin) using gitleaks. Each reported secret string
# is replaced with «REDACTED». If gitleaks is unavailable, text passes through
# unchanged — so capture still works, just without scrubbing.
_claude_ask_redact() {
  local text; text="$(cat)"
  local gl; gl="$(_claude_ask_gitleaks_bin)" || { print -r -- "$text"; return 0; }
  # Collect the matched secret strings (one per finding) via JSON report.
  local secrets
  secrets=$(print -r -- "$text" \
    | "$gl" stdin --report-format json --report-path - --no-banner 2>/dev/null \
    | grep '"Secret":' \
    | sed -E 's/.*"Secret": "(.*)",?$/\1/')
  [[ -z "$secrets" ]] && { print -r -- "$text"; return 0; }
  # Replace each found secret with a marker. Use zsh string replace (no regex,
  # so special chars in the secret are literal).
  local s
  while IFS= read -r s; do
    [[ -n "$s" ]] && text="${text//$s/«REDACTED»}"
  done <<< "$secrets"
  print -r -- "$text"
}

# Spinner on the tty until $1 (a pid) exits.
_claude_ask_spinner() {
  local pid=$1 frames='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏' i=0
  while kill -0 "$pid" 2>/dev/null; do
    printf '\r%s thinking…' "${frames:$((i % ${#frames})):1}" > /dev/tty
    i=$((i + 1))
    sleep 0.08
  done
  printf '\r\033[K' > /dev/tty   # clear the spinner line
}

# Core flow. $1 = "debug" to print captured context + assembled prompt before
# calling claude. Runs inside a ZLE widget context.
_claude_ask_run() {
  emulate -L zsh
  setopt local_options no_notify no_monitor
  local debug="$1"

  # Read the prompt without disturbing the user's command buffer.
  # NOTE: `vared` cannot be used here — it starts a nested ZLE session and zsh
  # rejects that ("can not be used recursively"). `read` is a plain builtin and
  # reads from the tty in cooked mode (backspace etc. handled by the terminal).
  local saved_buffer="$BUFFER" saved_cursor="$CURSOR"
  local prompt_text=""
  zle -I 2>/dev/null            # tell ZLE the display is now invalid
  local label='🤖 ask: '
  [[ "$debug" == debug ]] && label='🐞 ask (debug): '
  print -rn -- $'\n'"$label" > /dev/tty
  IFS= read -r prompt_text < /dev/tty

  if [[ -z "${prompt_text// }" ]]; then
    BUFFER="$saved_buffer"; CURSOR="$saved_cursor"
    zle reset-prompt
    return 0
  fi

  # Assemble context + question. Scrub secrets from scrollback before sending.
  local context full_prompt
  context="$(_claude_ask_context | _claude_ask_redact)"
  if [[ -n "$context" ]]; then
    full_prompt=$'Recent terminal output:\n'"$context"$'\n\nQuestion: '"$prompt_text"
  else
    full_prompt="$prompt_text"
  fi

  # Debug: show exactly what was captured and what will be sent.
  if [[ "$debug" == debug ]]; then
    {
      print -r -- $'\n──────── DEBUG ────────'
      local wt; wt="$(_claude_ask_wezterm_bin)" \
        && print -r -- "wezterm:  $wt" \
        || print -r -- "wezterm:  NOT FOUND (no scrollback context)"
      print -r -- "pane id:  ${WEZTERM_PANE:-<unset>}"
      local gl; gl="$(_claude_ask_gitleaks_bin)" \
        && print -r -- "gitleaks: $gl" \
        || print -r -- "gitleaks: NOT FOUND (secrets NOT redacted)"
      print -r -- "context:  ${#context} bytes, $(print -r -- "$context" | grep -c '') lines"
      print -r -- $'──── full prompt sent ────'
      print -r -- "$full_prompt"
      print -r -- $'───────────────────────\n'
    } > /dev/tty
  fi

  # System prompt: keep answers terminal-friendly. Always answer the question
  # directly; when a command is relevant, ALSO include it — never reply with a
  # command alone.
  local sys_prompt='You are a CLI assistant answering from a zsh terminal. Be concise. Always give the actual answer to the question. CRITICAL: whenever you run a shell command (or one is relevant) to obtain that answer, you MUST show the exact command in a fenced ```bash code block AND then give its result/explanation. Never present a result without the command that produced it, and never present a command without actually answering. End your response with two empty lines.'

  # Run claude in the background, capture combined output, show spinner.
  local out; out="$(mktemp "${TMPDIR:-/tmp}/claude-ask.XXXXXX")"
  claude -p "$full_prompt" --model haiku --append-system-prompt "$sys_prompt" > "$out" 2>&1 &
  local cpid=$!

  # Ctrl-C kills the call + spinner cleanly.
  trap 'kill "$cpid" 2>/dev/null' INT
  _claude_ask_spinner "$cpid"
  wait "$cpid"; local rc=$?
  trap - INT

  # Start the answer on a guaranteed-fresh line. Without this leading newline the
  # answer can begin mid-line (after the spinner clear) and the subsequent
  # `zle reset-prompt` repaint clobbers part of it — which made fenced code
  # blocks appear empty in normal mode but not in debug mode (the debug block
  # happened to leave the cursor on a fresh line first).
  print -r -- "" > /dev/tty
  if (( rc != 0 )); then
    print -r -- "❌ claude exited ($rc):" > /dev/tty
  fi
  _claude_ask_render "$(<"$out")" > /dev/tty   # render markdown via glow
  print -r -- $'\n' > /dev/tty   # spacing after the answer
  command rm -f "$out"

  # Restore the original command line.
  BUFFER="$saved_buffer"; CURSOR="$saved_cursor"
  zle reset-prompt
}

claude-ask-widget()       { _claude_ask_run; }
claude-ask-debug-widget() { _claude_ask_run debug; }

zle -N claude-ask-widget
zle -N claude-ask-debug-widget
bindkey '^x^a' claude-ask-widget          # Ctrl-X Ctrl-A : ask
bindkey '^x^g' claude-ask-debug-widget    # Ctrl-X Ctrl-G : ask + debug
