---
name: herdr
description: Control the Herdr app (desktop window) and herdr-core (`hc`) — spaces, sidebar sections, tabs, panes, terminals and coding agents. Use whenever the user mentions Herdr, a herdr space/workspace/section/tab/pane, or asks to start, read, message or wait on agents/terminals through Herdr.
---

# Herdr (app + herdr-core)

The user runs the **Herdr app** (`herdr-app`) on top of **herdr-core** (`hc`).
Do NOT use the legacy `herdr` CLI (`herdr workspace create`, `w1:p1` IDs,
`HERDR_ENV`) — that drives the old TUI, which is not what the user looks at.
Its `herdr workspace list` shows stale TUI workspaces, not the app's spaces.

## First step, every time

The installed binaries ship the authoritative, current manuals. Read the one
you need before acting (they change with app updates):

```sh
herdr-app --skill   # spaces, tabs, panes, layouts, mods — what the person sees
hc --skill          # running, reading, messaging, waiting on terminals/agents
herdr-app commands  # every app command + args (JSON)
```

Full file-level reference: `~/.config/herdr-app/AGENTS.md`.

## Vocabulary map (user words → app)

- "workspace" → a **space**: `herdr-app do space.new --name "<Name>" --folder <dir> --argv '["claude"]'`
  (returns `space`, `tab`, `terminal` IDs). Always pass an explicit name.
- "section" → a sidebar group of spaces in the `spaces-chat` mod. No command
  exists; it lives in `~/.config/herdr-app/shared.json` under
  `"spaces-chat".sections`: `{id: "sec-<8 random a-z0-9>", machine: null,
  name, folded: false, spaces: [<space id>]}`. Edit with a JSON round-trip
  (load, modify, atomic write via temp file + rename), never by hand-text; a
  space should be in at most one section. The app picks it up live.
- Inspect: `herdr-app ls` (spaces > tabs > terminals), `herdr-app status`.
- Select: `herdr-app do space.select --id <space id>`.

Default folder for act work: `~/git/act-security/act`. Default agent: `claude`.

## Safety

- Only create spaces/tabs when asked (they are shown immediately).
- Never close spaces, tabs or terminals you didn't create unless asked.
- Never stop/restart the app or the core (`hc server stop`).
- Don't edit `~/.config/herdr-app/AGENTS.md` or `*.d.ts` (the app rewrites them).
