# Agent Skills

chezmoi applies these to `~/.claude/skills/`. Anyone can install them without chezmoi.

| Skill | What it does | Needs |
| --- | --- | --- |
| [`explainer-artifact`](explainer-artifact/) | Visual, TLDR-first explainer page for a change, PR, or refactor. | `web-artifacts-builder`, `diagram-design`, Node 18+, python3, git |
| [`web-artifacts-builder`](web-artifacts-builder/) | React + shadcn/ui toolchain → one self-contained `bundle.html`. | Node 18+, pnpm or npm |
| [`chezmoi`](chezmoi/) | (`chezmoi-helper`) Templates, encryption, cross-machine setup. | chezmoi |
| [`dotfiles-sync`](dotfiles-sync/) | Syncs local config edits back into this repo. | chezmoi |
| [`wezterm-config`](wezterm-config/) | Edits and validates `wezterm.lua`. | WezTerm |
| [`herdr`](herdr/) | Controls the Herdr terminal multiplexer. | Herdr |

## Install

**Claude Code.** Dependencies install automatically:

```bash
claude plugin marketplace add IamShobe/dotfiles
claude plugin install explainer-artifact@iamshobe
# ✔ Successfully installed plugin: explainer-artifact@iamshobe (+ 2 dependencies: diagram-design, web-artifacts-builder)
```

**Whole terminal setup** (chezmoi-helper, dotfiles-sync, wezterm-config, herdr) in one install:

```bash
claude plugin install terminal-suite@iamshobe
```

It's a bundle: [`bundles/terminal-suite`](../../../bundles/terminal-suite/.claude-plugin/plugin.json)
holds only a `dependencies` list. If chezmoi already manages `~/.claude/skills`,
skip the bundle. Installing it too would load each skill twice.

**Cursor, Codex, opencode, and other agents.** Uses [`npx skills`](https://skills.sh):

```bash
npx skills add IamShobe/dotfiles --skill explainer-artifact -g
```

`npx skills` can't install dependencies yet ([vercel-labs/skills#515](https://github.com/vercel-labs/skills/issues/515)).
`explainer-artifact` covers that itself: on first run, `scripts/ensure-deps.sh`
fetches any missing skill into `explainer-artifact/.deps/`, installs the node
toolchain (~290MB, not committed), and installs the `explainer` diagram profile.
It takes about a minute, and later runs do nothing.

Update or remove:

```bash
claude plugin update explainer-artifact@iamshobe   # or: npx skills update
claude plugin uninstall explainer-artifact@iamshobe && claude plugin prune
```

## How dependencies are declared

No single standard covers every agent, so each dependency is declared in three places:

| Where | Read by | Effect |
| --- | --- | --- |
| `dependencies` in [`/.claude-plugin/marketplace.json`](../../../.claude-plugin/marketplace.json) | Claude Code | Installs dependencies automatically |
| `metadata.requires` + `compatibility` in `SKILL.md` | Any [Agent Skills](https://agentskills.io/specification) client, and people | Documents them only |
| `scripts/ensure-deps.sh` | The skill itself, at run time | Finds or fetches them. Works with any installer |

To add a dependency to a skill, update all three. A third-party skill also gets
its own entry in `marketplace.json` with a `github` source, like `diagram-design`.
That keeps it in the same marketplace, so Claude Code installs it without a
cross-marketplace allowlist.

## Editing

These are plain files in the chezmoi source. Edit them here, then apply:

```bash
chezmoi apply --force ~/.claude/skills
```

`home/.chezmoiignore` excludes `node_modules/`, `dist/` and `bundle.html`, so
`chezmoi apply` never deletes an installed toolchain.

Check the marketplace after changing it:

```bash
claude plugin validate .
```

## Conventions

- One directory per skill, each with a `SKILL.md` whose `description` says *when* to use it.
- The directory name matches the frontmatter `name`. `chezmoi/` → `chezmoi-helper` is a legacy exception.
- Keep `SKILL.md` short, and move detail into `references/`.
- Call scripts as `bash scripts/<name>.sh`. **Never use chezmoi's `executable_`
  prefix here.** Installers copy file names as they are, so the prefix breaks
  every documented script path.
