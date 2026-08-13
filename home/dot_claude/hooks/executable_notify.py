#!/usr/bin/env python3
"""Show tab indicator + macOS notification when Claude Code finishes."""
import json
import sys
import subprocess
import os
from pathlib import Path

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

# macOS notification, clicking activates WezTerm
text = user_msg if user_msg else "Response ready"

cmd = [
    "terminal-notifier",
    "-title", "Claude Code",
    "-message", text,
    "-activate", "com.github.wez.wezterm",
    "-contentImage", "file:///Applications/WezTerm.app/Contents/Resources/terminal.icns",
    "-sound", "Glass",
    "-group", "claude-code",             # replace previous notification, avoids throttling
]

subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
log_error(f"Notification dispatched: {text}")
