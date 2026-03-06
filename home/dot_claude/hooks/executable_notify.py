#!/usr/bin/env python3
"""Show tab indicator + macOS notification when Claude Code finishes."""
import json
import sys
import subprocess
import os
from pathlib import Path

WEZTERM = "/Applications/WezTerm.app/Contents/MacOS/wezterm"
LOG_FILE = Path.home() / ".local/share/a9s/notify-hook.log"

def log_error(msg: str):
    """Log errors to help diagnose hook failures."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(f"{msg}\n")
    except Exception:
        pass

try:
    payload = json.loads(sys.stdin.read())
except Exception as e:
    log_error(f"JSON parse failed: {e}")
    sys.exit(0)

transcript_path = payload.get("transcript_path")
log_error(f"Hook called with transcript_path={transcript_path}")

# Find last plain text user message
user_msg = ""
if transcript_path:
    try:
        with open(transcript_path) as f:
            lines = f.readlines()

        for line in reversed(lines):
            try:
                obj = json.loads(line)
                if obj.get("type") == "user":
                    msg = obj.get("message", {})
                    content = msg.get("content")
                    # Plain text message (not tool result array)
                    if isinstance(content, str) and content.strip():
                        user_msg = content[:60]
                        break
            except Exception:
                continue
    except Exception:
        pass

# 1. Update the WezTerm tab title using the CLI
pane_id = os.environ.get("WEZTERM_PANE")
tab_id = ""
base = ""
if pane_id:
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
                    tab_id = pane.get("tab_id", "")
                    break
        except Exception:
            pass
    # Determine base title — prefer tab_title (custom name), else process title
    base = tab_title or process_title
    for prefix in ["⟳ ", "✓ "]:
        if base.startswith(prefix):
            base = base[len(prefix):]
            break

    title = f"✓ {base}" if base else "✓ Done"
    result = subprocess.run(
        [WEZTERM, "cli", "set-tab-title", title, "--pane-id", pane_id],
        capture_output=True,
    )
    if result.returncode != 0:
        log_error(f"set-tab-title failed: {result.stderr}")
    else:
        log_error(f"Tab title updated to: {title}")

# 2. macOS notification (clickable — jumps back to the right tab/pane)
text = user_msg if user_msg else "Response ready"
hook_dir = Path(__file__).parent
focus_script = str(hook_dir / "focus-wezterm.sh")
execute_cmd = f"{focus_script} {pane_id} {tab_id}" if (pane_id and tab_id != "") else ""

cmd = [
    "terminal-notifier",
    "-title", "Claude Code",
    "-subtitle", base if base else "",   # tab name, e.g. "wezterm"
    "-message", text,
    "-activate", "com.github.wez.wezterm", # bring WezTerm to front on click (doesn't break -execute)
    "-contentImage", "file:///Applications/WezTerm.app/Contents/Resources/terminal.icns",
    "-sound", "Glass",
    "-group", "claude-code",             # replace previous notification, avoids throttling
]
if execute_cmd:
    cmd += ["-execute", execute_cmd]

result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    log_error(f"terminal-notifier failed: {result.stderr}")
    # Fallback to osascript
    script = f'display notification "{text}" with title "Claude Code" sound name "Glass"'
    subprocess.run(["osascript", "-e", script], capture_output=True)
else:
    log_error(f"Notification sent: {text}")
