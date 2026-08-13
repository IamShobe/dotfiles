---
name: Search tool preference
description: Always default to fast CLI search tools (ugrep/rg/fd) over grep and the Grep/Glob tools
type: feedback
---

Default to the fastest available CLI tool for search, always, not just when the built-in tool falls short:
- **`ugrep`** over plain `grep`/`rg` for any file/text search via Bash — SIMD-accelerated, faster on bulk scans. Installed via Homebrew (not mise — no aqua/cargo registry entry exists for it).
- **`rg`** via Bash instead of the Grep tool — the Grep tool has a fixed interface, `rg` is faster and more flexible.
- **`fd`** via Bash instead of the Glob tool — same reasoning, faster and more flexible.

**Why:** User wants command runtime minimized as a standing default ("use them always if possible, just in case — it's usually much more efficient"), not only when a task specifically demands it. Efficiency is the default posture, not a conditional fallback.

**How to apply:** Reach for `ugrep`/`rg`/`fd` via Bash by default for search tasks, even simple ones, rather than starting with `grep` or the Grep/Glob tools. Only fall back to the built-in tools if the fast CLI tool is unavailable in the environment.
