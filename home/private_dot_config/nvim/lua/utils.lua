local api = vim.api
local cmd = vim.cmd
local fn = vim.fn

local M = {}

M.guicursor = vim.o.guicursor
M.disableAutoMaximize = false
M.bufferDimNSId = api.nvim_create_namespace('buffer-dim')

-- make scratch buffer
function M.makeScratch()
  -- equivalent to :enew
  api.nvim_command('enew')
  -- set the current buffer's (buffer 0) buftype to nofile
  vim.bo[0].buftype = 'nofile'
  vim.bo[0].bufhidden = 'hide'
  vim.bo[0].swapfile = false
end

-- taken from https://github.com/neovim/neovim/issues/3688
function M.hideCursor()
  cmd('hi Cursor blend=100')

  -- for some reason unable to set through the M.opt
  cmd('set guicursor=' .. M.guicursor .. ',a:Cursor/lCursor')
end

function M.restoreCursor()
  cmd('hi Cursor blend=0')
  cmd('set guicursor=' .. M.guicursor)
end

local function windowIsRelative(windowId)
  return vim.api.nvim_win_get_config(windowId).relative ~= ''
end

local function windowIsCf(windowId)
  local buftype = vim.bo.buftype

  if windowId ~= nil then
    local bufferId = vim.api.nvim_win_get_buf(windowId)
    buftype = vim.api.nvim_buf_get_option(bufferId, 'buftype')
  end

  return buftype == 'quickfix'
end

local function windowIsToogleTerm()
  return vim.bo.filetype == 'toggleterm'
end

-- for auto command
function M.autoMaximizeWindow()
  if M.disableAutoMaximize or windowIsToogleTerm() or windowIsCf() then
    return
  end

  M.maximizeWindow()
end

-- togle autoMaximize
function M.toggleAutoMaximizeWindow()
  M.disableAutoMaximize = not M.disableAutoMaximize
end

local function toggleTermMaximize()
  local currentHeight = api.nvim_win_get_height(0)
  local defaultHeight = 15

  if currentHeight > defaultHeight then
    api.nvim_win_set_height(0, defaultHeight)
  else
    local totalHeight = vim.o.lines
    local nextHeight = totalHeight - defaultHeight

    api.nvim_win_set_height(0, math.max(nextHeight, defaultHeight))
  end
end

function M.maximizeWindow()
  -- resize only term
  if windowIsToogleTerm() then
    toggleTermMaximize()

    return
  end

  local currentWindowId = api.nvim_get_current_win()
  local windowsIds = api.nvim_list_wins()
  -- nothing to resize
  if #windowsIds < 2 or windowIsRelative(currentWindowId) then
    return
  end

  local minWidth = 15
  local totalWidth = 0
  local currentRow = vim.api.nvim_win_get_position(0)[1]
  local currentRowWindowIds = {}

  for _, id in ipairs(windowsIds) do
    if not windowIsRelative(id) then
      local y = vim.api.nvim_win_get_position(id)[1]
      if y == currentRow then
        totalWidth = totalWidth + api.nvim_win_get_width(id)
        table.insert(currentRowWindowIds, id)
      end
    end
  end

  local windowsInRow = #currentRowWindowIds

  -- nothing to resize
  if windowsInRow < 2 then
    return
  end

  local maximizedWidth = totalWidth - (windowsInRow - 1) * minWidth

  if
    maximizedWidth > minWidth and maximizedWidth > api.nvim_win_get_width(0)
  then
    for _, id in ipairs(currentRowWindowIds) do
      if id == currentWindowId then
        api.nvim_win_set_option(0, 'wrap', true)
        api.nvim_win_set_width(id, maximizedWidth)
      else
        api.nvim_win_set_option(id, 'wrap', false)
        api.nvim_win_set_width(id, minWidth)
      end
    end
  end
end

function M.toggleDimWindows()
  local windowsIds = api.nvim_list_wins()
  local currentWindowId = api.nvim_get_current_win()

  if windowIsRelative(currentWindowId) then
    return
  end

  pcall(vim.fn.matchdelete, currentWindowId)

  if windowIsCf(currentWindowId) then
    return
  end

  for _, id in ipairs(windowsIds) do
    if id ~= currentWindowId and not windowIsRelative(id) then
      pcall(fn.matchadd, 'BufDimText', '.', 200, id, { window = id })
    end
  end
end

return M