# User Preferences

## Git Commits
- **DO NOT** add "Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>" watermarks or similar footers to commit messages
- Keep commits clean and straightforward

# Projects

- [chezmoi: use `re-add`, not `add`](chezmoi-claude-settings-template.md) — `add` destroys templated sources like modify_settings.json.tmpl; `re-add` refuses to overwrite templates
- [chezmoi: don't double-prefix `home/` after cd'ing into source-path](chezmoi-source-path-git-prefix.md) — `source-path` already resolves inside `home/`; git paths from there are relative to it, no extra prefix
