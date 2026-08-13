#!/usr/bin/env python3
"""Display a pretty, information-dense status line in Claude Code."""
import json
import subprocess
import sys
from datetime import datetime

# ANSI color codes
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
RED = "\033[31m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def pct_color(pct):
    if pct is None:
        return DIM
    if pct > 85:
        return RED
    if pct > 60:
        return YELLOW
    return GREEN


def fmt_time_left(epoch_seconds):
    try:
        delta = epoch_seconds - datetime.now().timestamp()
        if delta <= 0:
            return None
        hours, rem = divmod(int(delta), 3600)
        minutes = rem // 60
        if hours >= 24:
            days, hours = divmod(hours, 24)
            return f"{days}d{hours}h"
        if hours:
            return f"{hours}h{minutes}m"
        return f"{minutes}m"
    except Exception:
        return None


def git_branch(cwd):
    try:
        result = subprocess.run(
            ["git", "-C", cwd, "status", "--porcelain=v2", "--branch"],
            capture_output=True, text=True, timeout=2,
        )
        if result.returncode != 0:
            return None
        branch = None
        dirty = False
        for line in result.stdout.splitlines():
            if line.startswith("# branch.head"):
                branch = line.split()[-1]
            elif not line.startswith("#"):
                dirty = True
        if branch is None or branch == "(detached)":
            return None
        return branch, dirty
    except Exception:
        return None


try:
    payload = json.loads(sys.stdin.read())
except Exception:
    sys.exit(0)

# ---- Line 1: model, directory, git branch ----
line1 = []

model = payload.get("model", {}).get("display_name", "")
if model:
    line1.append(f"{CYAN}◆{RESET} {BOLD}{model}{RESET}")

cwd = payload.get("workspace", {}).get("current_dir") or payload.get("cwd", "")
if cwd:
    dirname = cwd.rstrip("/").split("/")[-1] or "/"
    line1.append(f"{BLUE}📁{RESET} {dirname}")

git_info = git_branch(cwd) if cwd else None
if git_info:
    branch, dirty = git_info
    marker = f"{YELLOW}*{RESET}" if dirty else ""
    line1.append(f"{MAGENTA}⎇{RESET} {branch}{marker}")

# ---- Line 2: context %, rate limits, cost, lines changed ----
line2 = []

context_window = payload.get("context_window") or {}
used = context_window.get("used_percentage")
if used is not None:
    color = pct_color(used)
    line2.append(f"{color}◉{RESET} ctx {used:.0f}%")

rate_limits = payload.get("rate_limits") or {}
five_hour_data = rate_limits.get("five_hour", {})
seven_day_data = rate_limits.get("seven_day", {})
five_hour = five_hour_data.get("used_percentage")
seven_day = seven_day_data.get("used_percentage")
if five_hour is not None:
    color = pct_color(five_hour)
    left = fmt_time_left(five_hour_data.get("resets_at"))
    left_str = f" {DIM}({left} left){RESET}" if left else ""
    line2.append(f"{color}⏱{RESET} 5h {five_hour:.0f}%{left_str}")
if seven_day is not None:
    color = pct_color(seven_day)
    left = fmt_time_left(seven_day_data.get("resets_at"))
    left_str = f" {DIM}({left} left){RESET}" if left else ""
    line2.append(f"{color}📅{RESET} 7d {seven_day:.0f}%{left_str}")

cost = payload.get("cost") or {}
total_cost = cost.get("total_cost_usd")
if total_cost is not None:
    line2.append(f"{YELLOW}${total_cost:.2f}{RESET}")

sep = f" {DIM}│{RESET} "
print("  " + sep.join(line1))
if line2:
    print("  " + sep.join(line2))
