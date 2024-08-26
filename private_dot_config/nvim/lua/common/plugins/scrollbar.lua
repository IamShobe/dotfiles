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
