#!/usr/bin/env python3
"""Display a pretty usage status line in Claude Code."""
import json
import sys
import os
import subprocess
import tempfile
import time

def fmt_tokens(n):
    """Format tokens as K, M notation."""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)

try:
    payload = json.loads(sys.stdin.read())
except Exception:
    sys.exit(0)

transcript_path = payload.get("transcript_path")
if not transcript_path or not os.path.exists(transcript_path):
    sys.exit(0)

# Accumulate totals
totals = {
    "input_tokens": 0,
    "output_tokens": 0,
    "cache_read_input_tokens": 0,
    "cache_creation_input_tokens": 0,
}
model = ""

with open(transcript_path) as f:
    for line in f:
        try:
            obj = json.loads(line)
            if obj.get("type") == "assistant":
                msg = obj.get("message", {})
                if msg.get("role") == "assistant":
                    if msg.get("model"):
                        model = msg["model"]
                    usage = msg.get("usage", {})
                    if usage:
                        totals["input_tokens"] += usage.get("input_tokens", 0)
                        totals["output_tokens"] += usage.get("output_tokens", 0)
                        totals["cache_read_input_tokens"] += usage.get("cache_read_input_tokens", 0)
                        totals["cache_creation_input_tokens"] += usage.get("cache_creation_input_tokens", 0)
        except Exception:
            continue

# ANSI color codes
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Build pretty status line
parts = []

# Model with color
if model:
    model_short = model.split("-")[1] if "-" in model else model
    parts.append(f"{CYAN}◆{RESET} {BOLD}{model_short}{RESET}")

# Input tokens (blue)
parts.append(f"{BLUE}↓{RESET} {fmt_tokens(totals['input_tokens'])}")

# Output tokens (green)
parts.append(f"{GREEN}↑{RESET} {fmt_tokens(totals['output_tokens'])}")

# Cache stats (magenta)
cache_read = totals["cache_read_input_tokens"]
cache_write = totals["cache_creation_input_tokens"]
if cache_read or cache_write:
    parts.append(f"{MAGENTA}⚡{RESET} {fmt_tokens(cache_read)}/{fmt_tokens(cache_write)}")

# Context window usage (from payload)
context_window = payload.get("context_window", {})
if context_window:
    used = context_window.get("used_percentage", 0)
    # Color based on usage level
    if used > 85:
        color = "\033[31m"  # Red
    elif used > 60:
        color = "\033[33m"  # Yellow
    else:
        color = "\033[32m"  # Green
    parts.append(f"{color}◉{RESET} {used:.0f}%")

# Monthly spend from ccusage (cached for 5 minutes to avoid slowdown)
CACHE_FILE = os.path.join(tempfile.gettempdir(), "ccusage_monthly_cache.json")
CACHE_TTL = 300  # seconds

def get_monthly_spend():
    try:
        now = time.time()
        if os.path.exists(CACHE_FILE):
            age = now - os.path.getmtime(CACHE_FILE)
            if age < CACHE_TTL:
                with open(CACHE_FILE) as f:
                    cached = json.load(f)
                return cached.get("spend")
        result = subprocess.run(
            ["mise", "exec", "ccusage", "--", "ccusage", "monthly", "--json"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            print(f"ccusage error: {result.stderr}", file=sys.stderr)
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout.strip())
            # ccusage monthly --json returns {monthly: [...], totals: {...}}
            if isinstance(data, dict) and "monthly" in data:
                monthly = data["monthly"]
                if isinstance(monthly, list) and monthly:
                    entry = monthly[-1]  # most recent month
                else:
                    return None
            elif isinstance(data, list) and data:
                entry = data[-1]  # fallback: direct list
            elif isinstance(data, dict):
                entry = data  # fallback: direct dict
            else:
                return None
            spend = (entry.get("totalCost") or entry.get("cost") or
                     entry.get("total_cost") or entry.get("total"))
            if spend is None:
                return None
            with open(CACHE_FILE, "w") as f:
                json.dump({"spend": spend}, f)
            return spend
    except Exception:
        pass
    return None

monthly_spend = get_monthly_spend()
if monthly_spend is not None:
    parts.append(f"{YELLOW}${monthly_spend:.2f}{RESET}/mo")

# Join with nice separator
status = f"{DIM}│{RESET}  ".join(parts)
print(f"  {status}")
