@RTK.md

# GitHub

Use `gh` CLI for all GitHub work (authenticated as IamShobe). No GitHub MCP server — don't install/use one.

# chezmoi

`~` is chezmoi-managed (source: `~/.local/share/chezmoi`); some files are templates (`~/.claude/settings.json`, `~/.zshrc`, `~/.gitconfig`). Before editing anything under `~`, `~/.config`, `~/.claude`: run `chezmoi source-path <target>` and edit the source, not the target. Never `chezmoi add` an already-tracked file (destroys templates) — use `re-add`. Full procedure: `chezmoi` skill.

# Personal Obsidian vault

`~/vaults/personal` — personal-only knowledge, mirrored from personal Claude memories and checked for recall like memory is. Full rules: its `AGENTS.md` + `VAULT-INDEX.md`. Never work content.

# Memory

Global Claude memory lives at `~/.claude/memory/` (not `~/.claude/projects/*/memory/`, which is per-project-path and not chezmoi-synced).

# Signatures

Never add an AI signature/credit line to commits, PRs, comments — no `Co-Authored-By: Claude` or similar. Should read as if the user wrote it.
