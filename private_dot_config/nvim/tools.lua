local api = vim.api
local cmd = vim.cmd
local exec = vim.api.nvim_exec
local M = {}

local scopes = { o = vim.o, b = vim.bo, w = vim.wo, g = vim.g }

-- vim set helper
function M.opt(scope, key, value)
  scopes[scope][key] = value
  if scope ~= "o" then
    scopes["o"][key] = value
  end
end

-- vim keymap helper

function M.map(mode, lhs, rhs, opts)
  local options = { noremap = true }

  if opts then
    options = vim.tbl_extend("force", options, opts)
  end
  api.nvim_set_keymap(mode, lhs, rhs, options)
end

-- create auto groups
function M.createAugroup(autocmds, name)
  cmd("augroup " .. name)
  cmd("autocmd!")
  for _, autocmd in ipairs(autocmds) do
    cmd("autocmd " .. table.concat(autocmd, " "))
  end
  cmd("augroup END")
end

function M.hi(groupName, params)
  params = params or {}
  local highlightString = ""

  for k, v in pairs(params) do
    highlightString = highlightString .. string.format("  %s=%s", k, v)
  end

  exec("hi " .. groupName .. highlightString, false)
end

function M.hiLink(groupFrom, groupTo)
  exec("hi! link " .. groupFrom .. " " .. groupTo, false)
end

return M
