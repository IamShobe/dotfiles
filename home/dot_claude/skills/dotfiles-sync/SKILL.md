---
name: dotfiles-sync
description: |
  Sync local configuration file changes back to chezmoi dotfiles repository.
  Use this when you've edited Claude Code configs, wezterm, mise, or other tracked files locally
  and want to update your dotfiles repo to prevent drift.
  Also use when you suspect configuration drift and want to check what's out of sync.
  This skill detects changes, shows diffs, and auto-commits/pushes to your dotfiles repo.
---

# Dotfiles Sync Skill

Use this skill to keep your local configuration changes in sync with your chezmoi dotfiles repository.

## When to Use

- **After editing tracked files**: You've modified `~/.claude/hooks/`, `~/.claude/skills/`, `~/.claude/settings.json`, `~/.config/wezterm/wezterm.lua`, `~/.mise.toml`, or other chezmoi-managed configs
- **Prevent configuration drift**: Ensure your dotfiles repo stays up-to-date with your actual machine setup
- **Multi-machine setup**: Before switching machines, make sure all changes are committed to dotfiles

## Tracked Locations

The skill monitors these directories and files:
- `~/.claude/hooks/` - Claude Code hooks
- `~/.claude/skills/` - Custom skills
- `~/.claude/settings.json` - Claude Code settings
- `~/.claude/memory/` - Persistent memories
- `~/.config/wezterm/wezterm.lua` - WezTerm terminal config
- `~/.mise.toml` - Mise tool configuration

**Excluded** (intentionally not synced):
- `~/.claude/settings.local.json` - Machine-specific permissions
- `~/.claude/plans/`, `~/.claude/tasks/`, `~/.claude/projects/` - Work-in-progress
- `~/.claude/plugins/`, `~/.claude/cache/`, `~/.claude/file-history/` - Generated artifacts
- `~/.claude/ide/`, `~/.claude/shell-snapshots/`, `~/.claude/debug/` - Session-specific

## Workflow

1. **Check for changes**: Script scans tracked locations against chezmoi source
2. **Show diffs**: Displays what's different between local and dotfiles versions
3. **Detect new configs**: Identifies untracked global config files that might be useful to share
4. **Suggest additions**: Prompts you to add relevant new files to chezmoi tracking
5. **Confirm sync**: Asks you to review and approve all changes
6. **Auto-sync**: Commits changes with descriptive message and pushes to remote
7. **Report status**: Shows commit hash and push result

## Smart Config Detection

The skill detects common global configuration files that you might want to track:
- Shell configs: `.zshrc`, `.bashrc`, `.zshrc.d/`
- Git configs: `.gitconfig`, `.gitignore_global`
- SSH config: `.ssh/config`
- Editor configs: `~/.config/nvim/`, `~/.config/helix/`
- Tool configs: `~/.config/ripgrep/`, `~/.config/fd/`
- And more...

When new configs are found, the skill asks if you want to add them to chezmoi so they're available on all your machines.

## Expected Output

```
🔍 Scanning for changes in tracked files...

✏️  Modified files detected:
  ~/.claude/hooks/status.py
  ~/.config/wezterm/wezterm.lua

📋 Showing diffs:

=== ~/.claude/hooks/status.py ===
[diff output]

=== ~/.config/wezterm/wezterm.lua ===
[diff output]

✅ Sync these changes? (yes/no)
[After confirmation]

📦 Syncing to dotfiles...
✓ Copied 2 files to chezmoi
✓ Committed: "Update hooks and wezterm config"
✓ Pushed to origin/main

Done! All changes synced to dotfiles repo.
```

## Implementation

The skill uses helper scripts to:
1. Identify all chezmoi-tracked file locations
2. Compare local files with chezmoi source versions
3. Generate diffs
4. Handle git operations (commit and push)
5. Provide clear status feedback

When you invoke the skill, it automates the entire sync process with user confirmation at the diff review step.
