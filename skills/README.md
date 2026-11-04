# Agent Skills

This folder is the [skillshare](https://github.com/runkids/skillshare) source: `skillshare sync` links each skill into `~/.claude/skills/` (and any other agent you add as a target). Anyone can install them without skillshare.

| Skill | What it does | Needs |
| --- | --- | --- |
| [`explainer-artifact`](explainer-artifact/) | Visual, TLDR-first explainer page for a change, PR, or refactor. | `web-artifacts-builder`, `diagram-design`, Node 18+, python3, git |
| [`web-artifacts-builder`](web-artifacts-builder/) | React + shadcn/ui toolchain → one self-contained `bundle.html`. | Node 18+, pnpm or npm |
| [`no-smell`](no-smell/) | TypeScript/Python code standards, plus a hook that flags smells each edit introduces. | git, jq (for the hook) |
| [`chezmoi`](chezmoi/) | (`chezmoi-helper`) Templates, encryption, cross-machine setup. | chezmoi |
| [`dotfiles-sync`](dotfiles-sync/) | Syncs local config edits back into this repo. | chezmoi |
| [`wezterm-config`](wezterm## Install

Everything installs straight from this public repo. Pick the way that fits the agent.

### Claude Code: plugins (recommended)

Add the marketplace once, then install what you want. Dependencies come along automatically.

```bash
claude plugin marketplace add IamShobe/dotfiles

claude plugin install explainer-artifact@iamshobe
# ✔ Successfully installed plugin: explainer-artifact@iamshobe (+ 2 dependencies: diagram-design, web-artifacts-builder)

claude plugin install no-smell@iamshobe
# ✔ Successfully installed plugin: no-smell@iamshobe
```

- **`explainer-artifact`**: on first use, `scripts/ensure-deps.sh` finds the two dependencies,
  installs the node toolchain (~290MB, about a minute, once) and the `explainer` diagram profile.
- **`no-smell`**: the plugin also installs its `PostToolUse` hook, so every Edit/Write of a TS or
  Python file is scanned and Claude gets back only the smells that edit introduced. Needs `git`
  and `jq` on `PATH`.

**Whole terminal setup** (chezmoi-helper, dotfiles-sync, wezterm-config, herdr) in one install:

```bash
claude plugin install terminal-suite@iamshobe
```

It's a bundle: [`bundles/terminal-suite`](../bundles/terminal-suite/.claude-plugin/plugin.json)
holds only a `dependencies` list.

Update or remove:

```bash
claude plugin marketplace update iamshobe
claude plugin update explainer-artifact@iamshobe
claude plugin uninstall explainer-artifact@iamshobe && claude plugin prune
```

### Any agent (Claude Code, Codex, Cursor, opencode, …): skillshare

[skillshare](https://github.com/runkids/skillshare) installs from GitHub, records the source so
`skillshare update` keeps it current, and links the skills into every agent you add as a target.
Skills don't declare dependencies to each other, so install a skill's dependencies with it:

```bash
# explainer-artifact and its two dependencies
skillshare install IamShobe/dotfiles/skills/explainer-artifact -g
skillshare install IamShobe/dotfiles/skills/web-artifacts-builder -g
skillshare install cathrynlavery/diagram-design/skills/diagram-design -g

# no-smell
skillshare install IamShobe/dotfiles/skills/no-smell -g

skillshare sync
```

`ensure-deps.sh` doesn't download skills: if one is missing it stops and prints the install command.

A skills-folder install doesn't come with the `no-smell` hook. To get it in Claude Code, add this to
`~/.claude/settings.json`, with the path to wherever the skill is linked:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/skills/no-smell/scripts/hook.sh",
            "timeout": 15,
            "statusMessage": "no-smell scan"
          }
        ]
      }
    ]
  }
}
```

Don't combine the two ways for the same skill: the plugin and the linked skill would both load.

tifact@iamshobe   # or: skillshare update explainer-artifact
claude plugin uninstall explainer-artifact@iamshobe && claude plugin prune
```

## How dependencies are declared

No single standard covers every agent, so each dependency is declared in three places:

| Where | Read by | Effect |
| --- | --- | --- |
| `dependencies` in [`/.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json) | Claude Code | Installs dependencies automatically |
| `metadata.requires` + `compatibility` in `SKILL.md` | Any [Agent Skills](https://agentskills.io/specification) client, skillshare users, and people | Documents what to install |
| `scripts/ensure-deps.sh` | The skill itself, at run time | Finds them wherever they were installed; names the install command if one is missing |

To add a dependency to a skill, update all three. A third-party skill also gets
its own entry in `marketplace.json` with a `github` source, like `diagram-design`.
That keeps it in the same marketplace, so Claude Code installs it without a
cross-marketplace allowlist.

## Editing

These are plain files in this repo, outside chezmoi's `home/` root. skillshare links
each skill folder into `~/.claude/skills`, so edits are live. Run `skillshare sync`
after adding, renaming or removing a skill.

- Each skill's own `.gitignore` lists what's generated on the machine (`node_modules/`,
  `dist/`, `bundle.html`, `__pycache__/`).
- `.skillignore` keeps skillshare from treating `node_modules/` as skills.
- `.gitignore` here keeps out machine-local skills and the ones skillshare installs from
  their upstream repos. Those installs are recorded in `.metadata.json`; `skillshare install`
  with no arguments reinstalls them on a new machine.

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
