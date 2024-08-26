local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system({
    "git",
    "clone",
    "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git",
    "--branch=stable", -- latest stable release
    lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

local status_ok, lazy = pcall(require, "lazy")
if not status_ok then
  return
end

-- Start setup
lazy.setup({
  spec = {
    { "chriskempson/base16-vim", lazy = false, priority = 1000 }, -- colorscheme

    -- Dashboard (start screen)
    {
      "goolord/alpha-nvim",
      dependencies = { "kyazdani42/nvim-web-devicons" },
      config = function()
        require("alpha").setup(require("alpha.themes.theta").config)
      end,
    },

    -- git integration
    {
      "lewis6991/gitsigns.nvim",
      dependencies = { "nvim-lua/plenary.nvim", "kyazdani42/nvim-web-devicons" },
    }, -- show line modifications on left hand side

    { "nvim-lua/plenary.nvim" }, -- lua functions that many plugins use

    { "szw/vim-maximizer" }, -- maximizes and restores current window
    { "tpope/vim-surround" }, -- add, delete, change surroundings (it's awesome)
    { "inkarkat/vim-ReplaceWithRegister" }, -- replace with register contents using motion (gr + motion)
    { "numToStr/Comment.nvim" }, -- commenting with gc
    { "nvim-tree/nvim-tree.lua", dependencies = { "kyazdani42/nvim-web-devicons" } }, -- file explorer
    { "nvim-lualine/lualine.nvim" }, -- statusline
    { "akinsho/bufferline.nvim", version = "v4.*" }, -- bufferline

    -- fuzzy finder w/ telescope
    { "nvim-telescope/telescope-fzf-native.nvim", build = "make" },
    {
      "nvim-telescope/telescope.nvim",
      dependencies = {
        "nvim-telescope/telescope-fzf-native.nvim",
        "LinArcX/telescope-command-palette.nvim",
      },
    },

    -- managing & installing lsp servers, linters & formatters
    { "williamboman/mason.nvim" }, -- in charge of managing lsp servers, linters & formatters
    { "williamboman/mason-lspconfig.nvim" }, -- bridges gap b/w mason & lspconfig

    -- configuring lsp servers
    { "neovim/nvim-lspconfig" }, -- easily configure language servers
    { "hrsh7th/cmp-nvim-lsp" }, -- for autocomplete
    { "glepnir/lspsaga.nvim", branch = "main" }, -- enhanced lsp uis
    { "jose-elias-alvarez/typescript.nvim" }, -- additional functionality for typescript server (e.g. rename file & update imports)
    { "onsails/lspkind.nvim" }, -- vs-code like icons for autocompletion

    -- autocomplete
    {
      "hrsh7th/nvim-cmp",
      event = "InsertEnter",
      dependencies = {
        "hrsh7th/cmp-buffer", -- source for text in buffer
        "hrsh7th/cmp-path", -- source for file system paths
        "L3MON4D3/LuaSnip", -- snippet engine
        "rafamadriz/friendly-snippets", -- useful snippets
        "saadparwaiz1/cmp_luasnip", -- source for snippets
        "hrsh7th/cmp-nvim-lsp", -- source for lsp completions
      },
    },

    -- formatting & linting
    { "jose-elias-alvarez/null-ls.nvim" }, -- configure formatters & linters
    { "jayp0521/mason-null-ls.nvim" }, -- bridges gap b/w mason & null-ls

    -- treesitter
    { "nvim-treesitter/nvim-treesitter", build = ":TSUpdate" }, -- treesitter
    { "nvim-treesitter/nvim-treesitter-textobjects" }, -- treesitter textobjects
    { "nvim-treesitter/nvim-treesitter-refactor" }, -- treesitter refactor
    { "nvim-treesitter/playground" }, -- treesitter playground

    -- auto closing
    { "windwp/nvim-autopairs" }, -- auto pairs
    { "windwp/nvim-ts-autotag" }, -- auto close html tags

    -- scrollbar
    { "petertriho/nvim-scrollbar" },

    -- clipboard
    { "AckslD/nvim-neoclip.lua" },

    -- highlight
    { "RRethy/vim-illuminate" },

    -- navigation
    { "tpope/vim-repeat" },
    { "ggandor/leap.nvim" },
    { "matze/vim-move" },
  },
})
