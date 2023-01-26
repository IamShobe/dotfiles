local status, cinnamon = pcall(require, "cinnamon")
if not status then
  return
end

cinnamon.setup({
  extra_keymaps = true,
  override_keymaps = true,

  max_length = 500,
  scroll_limit = -1,
})

local status, scrollbar = pcall(require, "scrollbar")
if not status then
  return
end

scrollbar.setup()

local status, gitsigns = pcall(require, "scrollbar.handlers.gitsigns")
if not status then
  return
end

gitsigns.setup()
