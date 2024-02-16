-- set colorscheme to nightfly with protected call
-- in case it isn't installed
local status, _ = pcall(vim.cmd, "colorscheme base16-tomorrow-night")
if not status then
  print("Colorscheme not found!") -- print error if colorscheme not installed
  return
end

local createAugroup = require('tools').createAugroup
local hi = require('tools').hi

hi("VertSplit", { guibg = "NONE" }) -- remove background from vertical split
hi("NvimTreeIndentMarker", { guifg = "#3FC5FF" }) -- change tree indent marker color
hi('BufDimText', { guibg = 'NONE', guifg = "#000", guisp = "#444", gui = 'NONE' })
