---
name: herdr
description: Control the Herdr app (herdr-app + hc) with the Shepherdr layout — create workspaces (spaces) with their Assistant, sidebar sections, icons and pins, tabs, panes, terminals and agents. Use whenever the user mentions Herdr, a herdr workspace/space/section/tab/pane, or asks to start, read, message or wait on agents through Herdr.
---

# Herdr (app + Shepherdr)

The user runs the **Herdr app** (`herdr-app`, the window) on **herdr-core** (`hc`, which runs every
terminal and agent), with the **Shepherdr** layout on top (Assistant per space, tasks, sections).
Do NOT use the legacy `herdr` CLI (`herdr workspace create`, `w1:p1` IDs, `HERDR_ENV`): it drives
the old TUI, which isn't what the user looks at.

You're inside the app when `$HC_TERMINAL_ID` is set (your terminal's address, e.g. `t14`).

## First: the official manuals

The installed binaries ship the authoritative manuals and change with each update. Read the one
you need before acting; prefer them over anything below when they disagree.

```sh
herdr-app --skill    # the window: spaces, tabs, panes, layouts, mods, commands
hc --skill           # programs and agents: run, read, send, wait, templates, sub-agents
herdr-app commands   # every app command and its arguments (JSON)
```

`~/.config/herdr-app/AGENTS.md` is the full file-level reference (layouts, mods, keys).

## Look before acting

```sh
herdr-app ls         # spaces > tabs > terminals, with ids (use ids, never guess)
herdr-app status     # layout, focus, overlays, errors
herdr-app shot /path/to/shot.png   # what the window shows (read it to verify UI changes)
```

## New workspace (a space)

"Workspace" means a **space**. Make it with a name and folder and **no `--argv`**: Shepherdr sees
the new space and opens its **Assistant** tab itself (from `~/.config/herdr-core/templates`), and
a space an agent makes doesn't pull the user's view away. Passing `--argv '["claude"]'` adds a
second, plain agent beside the Assistant: don't.

```sh
herdr-app do space.new --name "DAG executor" --folder ~/git/act-security/act
```

- Worktree work: create the git worktree first (the user's convention: `~/.herdr/worktrees/<repo>/<branch>`),
  then `--folder` it. Every worktree is its own space; group related spaces with a section.
- **Always give it a fitting icon** right after creating it: one emoji that says what the work is
  (🕸️ a DAG/graph engine, 🔐 auth/SCIM, 🐛 a bug hunt, 📊 analytics, 🚀 a release, 🧪 an experiment):
  `herdr-sections icon <space-id> <emoji>` (id from `herdr-app ls`). Don't reuse another space's icon.
- Put it in a section right away when the user names one (below).
- `space.rename`, `space.move`, `space.select`, `space.close --confirmed true` (only spaces you made
  or the user asked to close).

## Sections, icons, pins (`herdr-sections`)

The sidebar's sections live in the app's shared state. Never edit `~/.config/herdr-app/shared.json`
by hand: the running app overwrites it. Use `herdr-sections` (it asks the `sections-api` mod to
make the change inside the app):

```sh
herdr-sections list
herdr-sections create "DAG executor" <space-id> [<space-id> ...]   # made if missing
herdr-sections move <space-id> "SCIM"          # or: move <space-id> --top
herdr-sections rename "SCIM" "SCIM v2"
herdr-sections delete "SCIM"                   # its spaces go back to the top
herdr-sections fold "SCIM" on|off
herdr-sections icon <space-id> 🎮              # or: icon <space-id> --none
herdr-sections pin <space-id> on|off
```

It prints `{ ok, sections }`. "Is Herdr running with the Shepherdr layout?" means the app is
closed or the layout lost its `sections-api` block (see Persistence).

## Tabs, panes, agents

- Tab per lane in one space: `herdr-app do tab.new --space <id> --name <lane> --folder <worktree> --argv '["claude"]'`
  (`--task "<first message>"` gives the agent its first prompt).
- Split: `herdr-app do pane.split --direction right|down --pane <pane-id> --argv '[...]'`.
- Close: `herdr-app do tab.close --id <tab-id> --confirmed true`.
- Background agents and commands: `hc run --bg --name <name> --cwd <dir> <template|program> "<task>"`,
  then `hc wait`, `hc read <name> --lines 80`, `hc send <name> "..."` — see `hc --skill`
  (templates: `hc templates`). Clean up only terminals you started.
- Shepherdr tasks (Assistant workflow, worktrees, Ready/Accept): `herdr-task --help`.

## Persistence (chezmoi)

Everything here is rebuilt on a new machine by the dotfiles repo:
Brewfile (`herdr-app` cask, `skillshare`), `run_onchange_after_8-install-herdr-shepherdr.sh.tmpl`
(Shepherdr at a pinned release + `.herdr/customize-shepherdr.py`: agents list, working spinner,
skillshare panel, `sections-api` holder, active layout), `~/.config/herdr-app/{keys,settings}.json`,
`mods/{skillshare,sections-api}`, `~/.local/bin/herdr-sections`.

- Changing a Shepherdr file (layout, a Shepherdr mod)? Change `.herdr/customize-shepherdr.py` in the
  chezmoi source instead, then run it: hand edits are lost on the next `shepherdr update`.
- Sections and spaces themselves are per-machine state, not backed up.

## Safety

- Only create spaces/tabs when asked; new ones show immediately.
- Never close what you didn't create unless asked; never stop the app or the core (`hc server stop`).
- Don't edit `AGENTS.md` or `*.d.ts` under `~/.config/herdr-app` (the app rewrites them).
