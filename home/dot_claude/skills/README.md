# Agent Skills

Skills live here and are applied to `~/.claude/skills/` by chezmoi. They also work
with Cursor, Codex, opencode and [70+ other agents](https://github.com/vercel-labs/skills#supported-agents)
via the [`skills`](https://skills.sh) CLI.

| Skill | What it does |
| --- | --- |
| [`explainer-artifact`](explainer-artifact/) | Visual, TLDR-first explainer page for a change/PR/refactor — written for teammates, not machines. |
| [`web-artifacts-builder`](web-artifacts-builder/) | Build toolchain: React + shadcn/ui + mermaid/recharts → one self-contained `bundle.html`. |
| [`chezmoi`](chezmoi/) | (`chezmoi-helper`) Templating, encryption, cross-machine dotfile setup. |
| [`dotfiles-sync`](dotfiles-sync/) | Syncs local config edits back into this repo to prevent drift. |
| [`wezterm-config`](wezterm-config/) | Edits and validates `wezterm.lua` — keybindings, fonts, themes. |

## Install (no chezmoi needed)

```bash
npx skills add IamShobe/dotfiles --list
npx skills add IamShobe/dotfiles --skill explainer-artifact -g -a claude-code
```

**`explainer-artifact` requires `web-artifacts-builder`** — install both:

```bash
npx skills add IamShobe/dotfiles \
  --skill explainer-artifact --skill web-artifacts-builder -g -a claude-code
```

The toolchain's `node_modules` (~290MB) is not committed. The first run bootstraps
it via `explainer-artifact/scripts/ensure-deps.sh` (~5s); later runs are no-ops.
Needs Node 18+ and pnpm (or npm).

## Editing

Edit here in the chezmoi source, then apply:

```bash
chezmoi edit --apply ~/.claude/skills/explainer-artifact/SKILL.md
```

`home/.chezmoiignore` excludes `node_modules/`, `dist/` and `bundle.html`, so
`chezmoi apply` never deletes an installed toolchain.

## Conventions

- One directory per skill, each with a `SKILL.md` whose frontmatter carries `name`
  and a `description` that states *when* to trigger it (that's what agents match on).
- Directory name should match the frontmatter `name` — `chezmoi/` declaring
  `chezmoi-helper` is a legacy exception.
- Keep `SKILL.md` short; push detail into `references/` and load it on demand.
- Scripts go in `scripts/` and are invoked as `bash scripts/<name>.sh` — don't rely
  on the executable bit, since it doesn't survive every install path.
