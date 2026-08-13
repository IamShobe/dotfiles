# User Preferences

## Git Commits
- **DO NOT** add "Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>" watermarks or similar footers to commit messages
- Keep commits clean and straightforward

## Tooling
- [No security/SSH commands](no-security-commands.md) — never run SSH/credential/GPG-touching commands, always defer to the user
- [Search tool preference](search-tool-preference.md) — use `rg`/`fd` via Bash over Grep/Glob tools when their fixed interface is insufficient
- [CLI tool stack](cli-tool-stack.md) — prefer zoxide/delta/sd/tokei/bottom/procs/ast-grep/difftastic (all mise-installed) over stock equivalents when the task fits

# Projects

- [chezmoi: use `re-add`, not `add`](chezmoi-claude-settings-template.md) — `add` destroys templated sources like modify_settings.json.tmpl; `re-add` refuses to overwrite templates
- [chezmoi: don't double-prefix `home/` after cd'ing into source-path](chezmoi-source-path-git-prefix.md) — `source-path` already resolves inside `home/`; git paths from there are relative to it, no extra prefix
