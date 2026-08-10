DOTFILES
========

## How to start?
Bootstrap:
```bash
curl https://raw.githubusercontent.com/IamShobe/dotfiles/main/bootstrap.sh | bash
```

OR:

```bash
chezmoi init IamShobe --apply
```

## To update
```bash
chezmoi update
```

## Daily commands - for using chezmoi
```bash
chezmoi add $FILE # adds $FILE from your home directory to the source directory.
chezmoi edit $FILE # opens your editor with the file in the source directory that corresponds to $FILE.
chezmoi status # gives a quick summary of what files would change if you ran chezmoi apply.
chezmoi diff # shows the changes that chezmoi apply would make to your home directory.
chezmoi apply # updates your dotfiles from the source directory.
chezmoi edit --apply $FILE # is like chezmoi edit $FILE but also runs chezmoi apply $FILE afterwards.
chezmoi cd # opens a subshell in the source directory.
```

## Agent Skills

This repo doubles as an [agent skills](https://skills.sh) source. The skills under
`home/dot_claude/skills/` work with Claude Code, Cursor, Codex, opencode and
[70+ other agents](https://github.com/vercel-labs/skills#supported-agents).

| Skill | What it does |
| --- | --- |
| `explainer-artifact` | Builds a visual, TLDR-first explainer page for a change/PR/refactor — for teammates, not machines. |
| `web-artifacts-builder` | The build toolchain: React + shadcn/ui + mermaid/recharts → one self-contained `bundle.html`. |
| `chezmoi-helper` | Working with chezmoi: templating, encryption, cross-machine setup. |
| `dotfiles-sync` | Syncs local config edits back into this repo to prevent drift. |
| `wezterm-config` | Edits and validates `wezterm.lua` — keybindings, fonts, themes. |

### Install (anyone)

You do **not** need chezmoi to use these — install just the skills you want:

```bash
# see what's available
npx skills add IamShobe/dotfiles --list

# install one, globally, for Claude Code
npx skills add IamShobe/dotfiles --skill explainer-artifact -g -a claude-code
```

> **`explainer-artifact` needs `web-artifacts-builder`** — install them together:
>
> ```bash
> npx skills add IamShobe/dotfiles \
>   --skill explainer-artifact --skill web-artifacts-builder -g -a claude-code
> ```

The build toolchain's `node_modules` (~290MB) is **not** committed. The first time
the skill runs it bootstraps itself via `scripts/ensure-deps.sh` (~5s with pnpm);
every run after that is a no-op. Requires Node 18+ and pnpm (or npm).

To update or remove:

```bash
npx skills update
npx skills remove explainer-artifact
```

### Install (me, via chezmoi)

`chezmoi apply` already places these in `~/.claude/skills/`. Edit them in the source
directory and re-apply:

```bash
chezmoi edit --apply ~/.claude/skills/explainer-artifact/SKILL.md
```

`node_modules`, `dist/` and `bundle.html` under any skill are listed in
`home/.chezmoiignore`, so `chezmoi apply` never deletes an installed toolchain.

## Manage tools with mise
```bash
mise add <tool>[@version]  # add a new tool
mise remove <tool>         # remove a tool
mise install               # install all tools in .mise.toml
mise ls installed          # list installed tools
```

Edit `~/.mise.toml` to add/remove tools, then run `mise install` to sync.

