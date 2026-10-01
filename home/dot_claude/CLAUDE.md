@RTK.md

# GitHub

Use `gh` CLI for all GitHub work (authenticated as IamShobe). No GitHub MCP server — don't install/use one.

# chezmoi

`~` is chezmoi-managed (source: `~/.local/share/chezmoi`); some files are templates (`~/.claude/settings.json`, `~/.zshrc`, `~/.gitconfig`). Editing anything under `~`, `~/.config`, `~/.claude` — even without the user saying "chezmoi" — invoke the `chezmoi` skill before touching the file; don't just run `source-path` from memory. Never `chezmoi add` an already-tracked file (destroys templates) — use `re-add`.

# Personal Obsidian vault

`~/vaults/personal` — personal-only knowledge, mirrored from personal Claude memories and checked for recall like memory is. Full rules: its `AGENTS.md` + `VAULT-INDEX.md`. Never work content.

# Memory

Global Claude memory lives at `~/.claude/memory/` (not `~/.claude/projects/*/memory/`, which is per-project-path and not chezmoi-synced).

# Signatures

Never add an AI signature/credit line to commits, PRs, comments — no `Co-Authored-By: Claude` or similar. Should read as if the user wrote it.

# Code standards (non-negotiable)

Before writing or editing TS/Python, invoke the `no-smell` skill and run its pre-handoff checklist before saying "done" or opening a PR. Short version:
- Branch on kinds with `ts-pattern` `.exhaustive()` — never `switch`, if-chains on the same field, or nested ternaries.
- Parse every boundary with zod/pydantic `safeParse`, one schema, strict. No `as` casts, no `any`, no string-parsing IDs.
- 2+ params → one destructured object (kwargs style).
- Entry function first, reads as a short story; helpers below in call order. Functional, verbose names.
- Use remeda / date-fns / cva / shadcn / tanstack-form / existing repo helpers instead of hand-rolling.
