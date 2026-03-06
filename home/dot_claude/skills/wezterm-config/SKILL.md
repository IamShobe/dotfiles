---
name: wezterm-config
description: Modify WezTerm configuration comprehensively. Use this skill whenever the user wants to customize WezTerm — add/modify keybindings (especially leader-key patterns), change fonts or font sizes, configure colors or themes, set up pane or tab behavior, add window decorations, configure domains, or adjust any setting in wezterm.lua. Also use this when the user gets errors about invalid keybindings or actions. The skill reads the current config, validates changes, applies them safely, and reloads WezTerm to verify they work.
compatibility: wezterm installed with config at ~/.config/wezterm/wezterm.lua
---

## Overview

This skill helps you modify WezTerm configuration comprehensively. It handles:
- **Keybindings**: Adding, modifying, or debugging keybindings (leader keys, chords, etc.)
- **Appearance**: Fonts, font size, colors, themes, window decorations
- **Behavior**: Pane/tab navigation, scrollback, copy mode, default programs
- **Domains**: SSH, multiplexing, local domain settings
- **Advanced**: Event handlers, custom Lua functions, performance tuning

The skill reads your current `~/.config/wezterm/wezterm.lua`, validates changes (checking that actions and keys exist), applies modifications, and provides feedback on what changed.

## How to use

Simply describe what you want to change in natural language:

**Examples:**
- "Add leader-key bindings for pane navigation: leader+h/j/k/l to move left/down/up/right"
- "Change the font to JetBrains Mono and increase size to 13"
- "Add a keybinding to toggle zoom with leader+z, and make sure it doesn't conflict"
- "I got an error about ActivateNextPane not existing — what's the right action for cycling panes?"
- "Configure Ctrl+S to save the scrollback to a file"
- "Add a custom color scheme called 'my-theme' with these colors..."
- "Set up an SSH domain for my server"

## What the skill does

1. **Reads your config** — Examines `~/.config/wezterm/wezterm.lua` to understand the current state
2. **Validates changes** — Checks that:
   - Keybinding actions exist in WezTerm (e.g., `SplitHorizontal` is real, `ActivateNextPane` is not)
   - Key names are valid (e.g., `UpArrow`, `Tab`, `a`, `F1`)
   - Modifier combinations are valid (e.g., `CTRL|SHIFT`)
3. **Applies modifications** — Edits the config file with proper Lua syntax
4. **Reloads WezTerm** — Triggers `Ctrl+Shift+R` to reload and verify changes work
5. **Explains the change** — Shows you what was added/modified and any validation issues

## Key WezTerm concepts to know

### Keybinding structure
```lua
{
  key = "key_name",          -- Single key: "a", "1", "Tab", "UpArrow", "F1", etc.
  mods = "CTRL|SHIFT",       -- Modifiers: CTRL, SHIFT, ALT, SUPER (combine with |)
  action = wezterm.action.ActionName({ params }),  -- The action to run
}
```

### Leader keys
A leader key is a prefix: press it, then release, then press the next key. Useful for chords.
```lua
config.leader = { key = "Space", mods = "CTRL", timeout_milliseconds = 1000 }
-- Then bind with mods = "LEADER"
```

### Common actions
- **Pane splits**: `SplitHorizontal`, `SplitVertical` (with `domain = "CurrentPaneDomain"`)
- **Pane navigation**: `ActivatePaneDirection("Up"|"Down"|"Left"|"Right")`
- **Pane management**: `CloseCurrentPane({ confirm = true })`, `TogglePaneZoomState`
- **Tab control**: `ActivateTab(0)`, `ActivateTabRelative(1)`, `ActivateLastTab`
- **Copy mode**: `ActivateCopyMode`
- **Command palette**: `ActivateCommandPalette`
- **Reload**: `ReloadConfiguration`
- **Send text**: `SendString("text")`
- **Spawn window**: `SpawnWindow`, `SpawnTab`
- **Quicksearch**: `QuickSelect`

For a full list of actions, consult WezTerm's action documentation or ask the skill to validate an action name.

### Config sections
Your wezterm.lua will have sections like:
- `config.font` — Font name (e.g., `"Menlo"`, `"JetBrains Mono"`)
- `config.font_size` — Size in points (e.g., `12`)
- `config.window_decorations` — `"INTEGRATED_BUTTONS|TITLE"` or `"NONE"`
- `config.colors` — Table of color overrides
- `config.leader` — Leader key configuration
- `config.keys` — Keybindings array
- `config.key_tables` — Custom key tables for modes (like tmux prefix)
- Event handlers (e.g., `wezterm.on("format-tab-title", ...)`)

## Validation & troubleshooting

**Invalid action**: The skill will tell you if an action doesn't exist and suggest alternatives. For example, `ActivateNextPane` isn't real — use `ActivatePaneDirection` instead.

**Key conflicts**: If you bind the same key twice with the same modifiers, the last one wins. The skill will warn you.

**Lua syntax errors**: The skill validates Lua syntax and will show errors before applying changes.

**Reload hangs**: If your config causes an infinite loop or hangs, use `Ctrl+C` to interrupt and describe the issue.

## Examples

### Leader-key pane splitting (tmux-style)
```
User: "Add tmux-style leader-key pane splits. Leader is Ctrl+Space. \ splits left/right, - splits top/bottom."
→ Skill adds config.leader and binds \ and - with the appropriate split actions.
```

### Navigation arrows
```
User: "Make leader+arrow keys navigate between panes."
→ Skill binds UpArrow, DownArrow, LeftArrow, RightArrow with LEADER mods to ActivatePaneDirection.
```

### Custom font
```
User: "Change font to 'Monaco' size 11."
→ Skill updates config.font and config.font_size.
```

### Debugging
```
User: "I got an error about ActivateNextPane. What should I use to cycle through panes?"
→ Skill explains that ActivateNextPane doesn't exist, suggests ActivatePaneDirection or sending keys.
```

## Tips

- **Organize keybindings**: Group related bindings together with comments (e.g., `-- Pane management`, `-- Tab control`)
- **Use descriptive comments**: Help future you understand why a binding exists
- **Test incrementally**: Add a few bindings, reload, test them, then add more
- **Avoid shadows**: Don't rebind keys that WezTerm uses by default (unless intentional)
- **Domain awareness**: When splitting panes, use `domain = "CurrentPaneDomain"` to inherit the current domain (useful for SSH domains)

## Limitations

- The skill modifies `~/.config/wezterm/wezterm.lua` directly — keep backups if you're paranoid
- Complex Lua code (custom event handlers, loops) should be added carefully; the skill can help, but you may need to refine
- Color schemes and fonts must already be installed/available on your system
- Some advanced WezTerm features (multiplexing, scripting) may require reading WezTerm docs for context
