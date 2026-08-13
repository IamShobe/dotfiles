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

# Signatures

Never add an AI/agent signature or credit line to anything written on the user's behalf — no `Co-Authored-By: Claude ...` (or any model name) footer on commits, no "generated with Claude Code" or similar in PR descriptions, issue comments, or code comments. Commits, PRs, and comments should read as if the user wrote them.
