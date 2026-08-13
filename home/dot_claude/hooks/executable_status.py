#!/usr/bin/env python3
"""Display a pretty, information-dense status line in Claude Code."""
import json
import os
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


def fmt_tokens(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def context_used_tokens(transcript_path):
    """Sum input+cache tokens of the most recent assistant usage entry.

    Context usage reflects the last turn's total context, not a running
    sum across turns, so only the latest usage snapshot is used.
    """
    if not transcript_path or not os.path.exists(transcript_path):
        return None
    last_usage = None
    try:
        with open(transcript_path) as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if obj.get("type") != "assistant":
                    continue
                msg = obj.get("message", {})
                usage = msg.get("usage")
                if usage:
                    last_usage = usage
    except Exception:
        return None
    if not last_usage:
        return None
    return (
        last_usage.get("input_tokens", 0)
        + last_usage.get("cache_read_input_tokens", 0)
        + last_usage.get("cache_creation_input_tokens", 0)
    )


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

pr = payload.get("pr") or {}
pr_number = pr.get("number")
pr_url = pr.get("url")
if pr_number:
    label = f"{CYAN}⇄{RESET} #{pr_number}"
    if pr_url:
        label = f"\033]8;;{pr_url}\033\\{label}\033]8;;\033\\"
    line1.append(label)

# ---- Line 2: context %, rate limits, cost, lines changed ----
line2 = []

context_window = payload.get("context_window") or {}
used = context_window.get("used_percentage")
if used is not None:
    color = pct_color(used)
    tokens = context_used_tokens(payload.get("transcript_path"))
    tokens_str = f" ({fmt_tokens(tokens)})" if tokens is not None else ""
    line2.append(f"{color}◉{RESET} ctx {used:.0f}%{tokens_str}")

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
