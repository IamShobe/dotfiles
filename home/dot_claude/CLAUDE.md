@RTK.md

# GitHub

Use the `gh` CLI for all GitHub work (issues, PRs, repos, releases, etc.) — already authenticated as IamShobe with repo scope. Do not use a GitHub MCP server; none is configured, and `github-mcp-server`/the GitHub Copilot MCP plugin should not be installed or relied on.

# chezmoi

Dotfiles are managed by chezmoi (source: `~/.local/share/chezmoi`). Several tracked files are templates — `~/.claude/settings.json` (a `modify_` script), `~/.zshrc`, `~/.gitconfig`, `~/.tmux.conf`.

**Never run `chezmoi add` on an already-tracked file.** It replaces the source with a static snapshot, silently deleting template logic and breaking anything that `include`s it. Check first, then pick the path:

```bash
chezmoi source-path <target>    # ends in .tmpl, or basename starts modify_/create_/run_ ?
```

- **Templated** → edit that source file directly with normal file tools, then `chezmoi apply --force <target>`. Do not use `chezmoi edit`; it opens `$EDITOR` and hangs without a TTY.
- **Plain** → `chezmoi re-add <target>`. Prefer `re-add` over `add` as the default verb: it refuses to overwrite templates instead of destroying them.

Verify by rendering, never by reading the target: `chezmoi cat <target>` (or `chezmoi execute-template < <source.tmpl>`). Reading the target only shows the last-applied state.

All chezmoi commands need `--force` here — there is no TTY, so prompts fail with "could not open a new TTY".

Never edit `~/.claude/settings.json` or other managed targets directly; the next `apply` overwrites them. Change the source and apply.

# Signatures

Never add an AI/agent signature or credit line to anything written on the user's behalf — no `Co-Authored-By: Claude ...` (or any model name) footer on commits, no "generated with Claude Code" or similar in PR descriptions, issue comments, or code comments. Commits, PRs, and comments should read as if the user wrote them.
