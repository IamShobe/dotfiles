#!/bin/bash
# Called by terminal-notifier -execute when notification is clicked.
# Args: <pane_id> <tab_id>
PANE_ID="$1"
TAB_ID="$2"
WEZTERM="/Applications/WezTerm.app/Contents/MacOS/wezterm"

# Bring WezTerm to foreground first so CLI commands can target the live window
open -a WezTerm

# Switch to the right tab then focus the specific pane
"$WEZTERM" cli activate-tab --tab-id "$TAB_ID" 2>/dev/null
"$WEZTERM" cli activate-pane --pane-id "$PANE_ID" 2>/dev/null

# Play a success sound
afplay /System/Library/Sounds/Ping.aiff 2>/dev/null &
