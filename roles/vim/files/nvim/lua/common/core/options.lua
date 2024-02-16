local opt = vim.opt -- for conciseness

-- disable default mode showing
opt.showmode = false

opt.laststatus = 2 -- always display status

-- modelines
opt.modelines = 5

-- line numbers
opt.relativenumber = false -- show relative line numbers
opt.number = true -- shows absolute line number on cursor line (when relative number is on)

-- tabs & indentation
opt.tabstop = 2 -- 2 spaces for tabs (prettier default)
opt.shiftwidth = 2 -- 2 spaces for indent width
opt.expandtab = true -- expand tab to spaces
opt.smarttab = true
opt.autoindent = true -- copy indent from current line when starting new one

-- line wrapping
opt.wrap = false -- disable line wrapping

-- search settings
opt.ignorecase = true -- ignore case when searching
opt.smartcase = true -- if you include mixed case in your search, assumes you want case-sensitive

-- cursor line
opt.cursorline = true -- highlight the current cursor line

-- appearance

-- turn on termguicolors for nightfly colorscheme to work
-- (have to use iterm2 or any other true color terminal)
opt.termguicolors = true
opt.background = "dark" -- colorschemes that can be light or dark will be made dark
opt.signcolumn = "yes" -- show sign column so that text doesn't shift

-- backspace
opt.backspace = "indent,eol,start" -- allow backspace on indent, end of line or insert mode start position

-- clipboard
-- opt.clipboard:append("unnamedplus") -- use system clipboard as default register

-- split windows
opt.splitright = true -- split vertical window to the right
opt.splitbelow = true -- split horizontal window to the bottom

opt.iskeyword:append("-") -- consider string-string as whole word

local create_dir = function(path)
  if not vim.fn.isdirectory(path) then
    local status, _ = pcall(vim.cmd, "mkdir(" .. path .. ", '', 0700)")
    if not status then
      print("directory not created!")
      return false
    end
  end

  return true
end

local base_dir = vim.fn.stdpath("data") .. "/cache"
local swap_file_dir = base_dir .. "/swapfiles/"
local undo_file_dir = base_dir .. "/undo/"

-- swap files
if not create_dir(swap_file_dir) then
  print("failed creating swap directory!")
else
  opt.directory = swap_file_dir
end

-- undo files
if not create_dir(undo_file_dir) then
  print("failed creating undo directory!")
else
  opt.undodir = undo_file_dir
  opt.undofile = true
end

opt.updatetime = 100

opt.fillchars = 'eob: '
