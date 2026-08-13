@RTK.md

# GitHub

Use the `gh` CLI for all GitHub work (issues, PRs, repos, releases, etc.) — already authenticated as IamShobe with repo scope. Do not use a GitHub MCP server; none is configured, and `github-mcp-server`/the GitHub Copilot MCP plugin should not be installed or relied on.

# chezmoi

Global config is managed by chezmoi (source: `~/.local/share/chezmoi`). Some tracked files are templates, including `~/.claude/settings.json` (a `modify_` script), `~/.zshrc`, `~/.gitconfig`.

- **Before editing any file in `~`, `~/.config`, or `~/.claude`**, run `chezmoi source-path <target>`. If it resolves, chezmoi owns the file: edit the **source** and `chezmoi apply --force <target>`. Never edit a managed target directly — the next `apply` overwrites it.
- **Never run `chezmoi add` on an already-tracked file.** It snapshots the target over the source, silently destroying templates. Use `chezmoi re-add` for plain files; edit the source directly for templated ones. `add` is only for new, untracked files.
- Untracked but durable global config should generally be brought under chezmoi — propose it, don't do it silently. Machine-local state (caches, credentials) stays untracked.
- Pass `--force`; there is no TTY here. Verify with `chezmoi cat <target>`, not by reading the target.

The `chezmoi` skill has the full procedures, template details, and recovery steps.

# Personal Obsidian vault

`~/vaults/personal` is a git-backed Obsidian vault for the user's personal
knowledge (see its `AGENTS.md` for full rules — read it before writing there).
Applies in every session, any working directory, not just when already inside
that folder:

- **Read `~/vaults/personal/VAULT-INDEX.md` first**, before grepping the
  vault — it's a live summary of what exists (notes, open threads, recent
  changes), kept current on every write. Don't rediscover the vault from
  scratch when the index already has the answer.
- Whenever a Claude memory entry is saved and it is clearly personal — not
  tied to a specific work project, employer, or repo — also write or update
  a corresponding note in `~/vaults/personal`, following that vault's
  `AGENTS.md` template and filing rules. If ambiguous whether it's personal
  or work-related, skip mirroring rather than ask.
- **After any write, update `VAULT-INDEX.md`** (Notes list + "Recently
  touched") in the same turn — it must never drift out of sync with what's
  actually in the vault.
- At the end of a session, do a quick pass for anything personal and
  vault-worthy that wasn't already mirrored, and file it then. Skip silently
  if there's nothing to add.
- Never write work content into this vault. When in doubt, don't.
- **Recall**: whenever something in a session would prompt checking Claude
  memory for relevance, check `VAULT-INDEX.md` first, then the relevant
  note(s) directly (no MCP needed). Treat it as a second, equally-weighted
  source, not a fallback only checked when memory comes up empty.

# Signatures

Never add an AI/agent signature or credit line to anything written on the user's behalf — no `Co-Authored-By: Claude ...` (or any model name) footer on commits, no "generated with Claude Code" or similar in PR descriptions, issue comments, or code comments. Commits, PRs, and comments should read as if the user wrote them.
