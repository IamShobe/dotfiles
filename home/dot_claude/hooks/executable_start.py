#!/usr/bin/env python3
"""Set WezTerm tab prefix to ⟳ when Claude Code starts working."""
import subprocess
import os
import json

WEZTERM = "/Applications/WezTerm.app/Contents/MacOS/wezterm"

pane_id = os.environ.get("WEZTERM_PANE")
if not pane_id:
    exit(0)

process_title = ""
tab_title = ""
result = subprocess.run(
    [WEZTERM, "cli", "list", "--format", "json"],
    capture_output=True, text=True,
)
if result.returncode == 0:
    try:
        for pane in json.loads(result.stdout):
            if str(pane.get("pane_id")) == pane_id:
                process_title = pane.get("title", "")
                tab_title = pane.get("tab_title", "")
                break
    except Exception:
        pass

# Determine base title — prefer tab_title (custom name), else process title
base = tab_title or process_title
for prefix in ["⟳ ", "✓ "]:
    if base.startswith(prefix):
        base = base[len(prefix):]
        break

title = f"⟳ {base}" if base else "⟳ Working"
subprocess.run(
    [WEZTERM, "cli", "set-tab-title", title, "--pane-id", pane_id],
    capture_output=True,
)
