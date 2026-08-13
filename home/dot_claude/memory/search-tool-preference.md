---
name: Search tool preference
description: When to use rg via Bash vs the Grep tool for searching
type: feedback
---

Use `rg` via Bash instead of the Grep tool when the task requires it (complex flags, piping, custom output formats, etc.). The Grep tool has a fixed interface and is more limited than running `rg` directly.

Use `fd` via Bash instead of the Glob tool when the task requires it (complex filters, type flags, exec, etc.). The Glob tool has a fixed interface and is more limited than running `fd` directly.

**Why:** Both the Grep and Glob tools have constrained APIs that can't express everything `rg`/`fd` support natively. They work differently from their CLI counterparts.

**How to apply:** Default to the dedicated tools (Grep/Glob) for simple cases, but switch to `rg`/`fd` via Bash whenever the dedicated tool's interface is insufficient.
