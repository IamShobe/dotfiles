local wezterm = require("wezterm")
local config = wezterm.config_builder()

-- Basic config
config.font = wezterm.font("Menlo")
config.font_size = 12
config.enable_kitty_keyboard = true

-- Configure tab title to show zoom state
wezterm.on("format-tab-title", function(tab, tabs, panes, config, hover, max_width)
  local title = tab.tab_title
  if not title or #title == 0 then
    title = tab.active_pane.title
  end
  if not title then
    title = "untitled"
  end
  local zoom_indicator = ""

  -- Check if the active pane in this tab is zoomed
  if tab.active_pane.is_zoomed then
    zoom_indicator = " 🔍"
  end

  local text = title .. zoom_indicator

  if hover then
    return {
      { Attribute = { intensity = "bold" } },
      { Text = " " .. text .. " " },
    }
  end

  return {
    { Text = " " .. text .. " " },
  }
end)

-- Configure leader key (Ctrl+Space)
config.leader = { key = "Space", mods = "CTRL", timeout_milliseconds = 2000 }

-- Configure mouse bindings: require Cmd+click to open hyperlinks and email addresses
config.mouse_bindings = {
  -- Override default plain-click: selection only, never open links
  {
    event = { Up = { streak = 1, button = "Left" } },
    mods = "NONE",
    action = wezterm.action.CompleteSelection("ClipboardAndPrimarySelection"),
  },
  -- Cmd+click to open links (URLs and emails)
  {
    event = { Up = { streak = 1, button = "Left" } },
    mods = "SUPER",  -- Cmd key on macOS
    action = wezterm.action.OpenLinkAtMouseCursor,
  },
  -- Suppress Down event of Cmd-click to avoid weird program behavior
  {
    event = { Down = { streak = 1, button = "Left" } },
    mods = "SUPER",
    action = wezterm.action.Nop,
  },
}

-- Add keybinding to reload config
config.keys = {
  {
    key = "v",
    mods = "SUPER",
    action = wezterm.action.EmitEvent("smart-paste"),
  },
  {
    key = "r",
    mods = "CTRL|SHIFT",
    action = wezterm.action.ReloadConfiguration,
  },
  {
    key = '"',
    mods = "LEADER",
    action = wezterm.action.SplitVertical({ domain = "CurrentPaneDomain" }),
  },
  {
    key = "%",
    mods = "LEADER",
    action = wezterm.action.SplitHorizontal({ domain = "CurrentPaneDomain" }),
  },
  -- Pane management
  {
    key = "x",
    mods = "LEADER",
    action = wezterm.action.CloseCurrentPane({ confirm = true }),
  },
  {
    key = "z",
    mods = "LEADER",
    action = wezterm.action.TogglePaneZoomState,
  },
  {
    key = "d",
    mods = "LEADER",
    action = wezterm.action.CloseCurrentPane({ confirm = true }),
  },
  -- Tab management
  {
    key = ",",
    mods = "LEADER",
    action = wezterm.action.PromptInputLine({
      description = "Rename tab:",
      action = wezterm.action_callback(function(window, pane, line)
        if line then
          window:active_tab():set_title(line)
        end
      end),
    }),
  },
  -- Arrow key navigation with leader
  {
    key = "UpArrow",
    mods = "LEADER",
    action = wezterm.action.ActivatePaneDirection("Up"),
  },
  {
    key = "DownArrow",
    mods = "LEADER",
    action = wezterm.action.ActivatePaneDirection("Down"),
  },
  {
    key = "LeftArrow",
    mods = "LEADER",
    action = wezterm.action.ActivatePaneDirection("Left"),
  },
  {
    key = "RightArrow",
    mods = "LEADER",
    action = wezterm.action.ActivatePaneDirection("Right"),
  },
}

-- Smart paste: if clipboard has an image, save it and paste the path
wezterm.on("smart-paste", function(window, pane)
  local image_path = "/tmp/wezterm_clipboard_" .. os.time() .. ".png"
  local ok, success = pcall(function()
    return wezterm.run_child_process({ "/opt/homebrew/bin/pngpaste", image_path })
  end)
  if ok and success then
    window:perform_action(wezterm.action.SendString(image_path), pane)
  else
    window:perform_action(wezterm.action.PasteFrom("Clipboard"), pane)
  end
end)

-- Show notification when config reloads
wezterm.on("window-config-reloaded", function(window, pane)
  window:set_right_status("config reloaded ✓")
  wezterm.log_info("Setting timer to clear status")
  wezterm.time.call_after(2, function()
    wezterm.log_info("Timer fired, clearing status")
    window:set_right_status("")
  end)
end)

return config
