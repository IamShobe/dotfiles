# Panes bound to a Coder workspace (HERDR_CODER_WS set at pane creation) resolve
# `claude` to the remote shim, keeping herdr's agent tracking working over SSH.
# Must run after mise activation, which rebuilds PATH.
if [[ -n "${HERDR_CODER_WS:-}" ]]; then
  path=("$HOME/.local/libexec/herdr-coder-shim" $path)
fi
