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

claude-ask-widget() {
  emulate -L zsh
  setopt local_options no_notify no_monitor

  # Read the prompt without disturbing the user's command buffer.
  # NOTE: `vared` cannot be used here — it starts a nested ZLE session and zsh
  # rejects that ("can not be used recursively"). `read` is a plain builtin and
  # reads from the tty in cooked mode (backspace etc. handled by the terminal).
  local saved_buffer="$BUFFER" saved_cursor="$CURSOR"
  local prompt_text=""
  zle -I 2>/dev/null            # tell ZLE the display is now invalid
  print -rn -- $'\n🤖 ask: ' > /dev/tty
  IFS= read -r prompt_text < /dev/tty

  if [[ -z "${prompt_text// }" ]]; then
    BUFFER="$saved_buffer"; CURSOR="$saved_cursor"
    zle reset-prompt
    return 0
  fi

  # Assemble context + question.
  local context full_prompt
  context="$(_claude_ask_context)"
  if [[ -n "$context" ]]; then
    full_prompt=$'Recent terminal output:\n'"$context"$'\n\nQuestion: '"$prompt_text"
  else
    full_prompt="$prompt_text"
  fi

  # System prompt: keep answers terminal-friendly. Always answer the question
  # directly; when a command is relevant, ALSO include it — never reply with a
  # command alone.
  local sys_prompt='You are a CLI assistant answering from a zsh terminal. Be concise. Always answer the question directly with the actual information or explanation. When a shell command is relevant, ALSO include it in a fenced code block in addition to your answer — never reply with only a command and no explanation. add 2 empty lines in the end'

  # Run claude in the background, capture combined output, show spinner.
  local out; out="$(mktemp "${TMPDIR:-/tmp}/claude-ask.XXXXXX")"
  claude -p "$full_prompt" --model haiku --append-system-prompt "$sys_prompt" > "$out" 2>&1 &
  local cpid=$!

  # Ctrl-C kills the call + spinner cleanly.
  trap 'kill "$cpid" 2>/dev/null' INT
  _claude_ask_spinner "$cpid"
  wait "$cpid"; local rc=$?
  trap - INT

  if (( rc != 0 )); then
    print -r -- "❌ claude exited ($rc):" > /dev/tty
  fi
  print -r -- "$(<"$out")" > /dev/tty
  command rm -f "$out"

  # Restore the original command line.
  BUFFER="$saved_buffer"; CURSOR="$saved_cursor"
  zle reset-prompt
}

zle -N claude-ask-widget
bindkey '^x^a' claude-ask-widget
