set laststatus=2   " always display status
set t_Co=256       " terminal colors
set encoding=utf-8 " file encoding
set number         " line numbers
set nowrap         " test
set noshowmode     " disable default mode showing -- NORMAL --

set modeline       " will run vim command at start of files
set modelines=5    " 5 lines from the top and bottom of the files

set foldlevel=20   " start with all folds open until given value
set tabstop=4      " existing tabs will be shown as given value spaces
set softtabstop=4
set shiftwidth=4   " using shift+> will move given value amount spaces
set expandtab      " entering tab is translated to space
set smarttab 
set backspace=indent,eol,start
set mouse=a

let base16colorspace=256

if !exists('g:airline_symbols')
    let g:airline_symbols = {}
endif

silent! source $VIM_HOME/airline.vim
silent! colorscheme base16-tomorrow-night
let g:airline_theme="base16_tomorrow_night"

function! s:addSwapfiles(path)
    if !isdirectory(a:path)
        call mkdir(a:path, "", 0700)
    endif
    let &directory=a:path
endfunction

function! s:addUndodir(path)
    if !isdirectory(a:path)
        call mkdir(a:path, "", 0700)
    endif
    let &undodir=a:path
    set undofile
endfunction

if has('nvim')
  call s:addSwapfiles($VIM_HOME."/nswapfiles/")
  call s:addUndodir($VIM_HOME."/nundodir/")
else
  call s:addSwapfiles($VIM_HOME."/swapfiles/")
  call s:addUndodir($VIM_HOME."/undodir/")
endif 

silent! source $VIM_HOME/autocomplete.vim
let g:gitgutter_preview_win_floating = 1
let g:gitgutter_highlight_linenrs = 1
let g:gitgutter_preview_win_floating = 1
set updatetime=100  " for updating file status

let g:NERDDefaultAlign = 'left'
let g:NERDCompactSexyComs = 1
let g:NERDSpaceDelims = 1
let g:NERDCommentEmptyLines = 1


let g:rehash256 = 1
let g:python_highlight_all = 1
syntax enable


source $VIM_HOME/shortcuts.vim

set secure
let g:secure_modelines_allowed_items = [
    \ "textwidth",       "tw",
    \ "softtabstop",     "sts",
    \ "tabstop",         "ts",
    \ "shiftwidth",      "sw",
    \ "expandtab",       "et",        "noexpandtab",    "noet",
    \ "filetype",        "ft",
    \ "foldmethod",      "fdm",
    \ "formatoptions",   "fo",
    \ "readonly",        "ro",        "noreadonly",     "noro",
    \ "rightleft",       "rl",        "norightleft",    "norl",
    \ "cindent",         "cin",       "nocindent",      "nocin",
    \ "smartindent",     "si",        "nosmartindent",  "nosi",
    \ "autoindent",      "ai",        "noautoindent",   "noai",
    \ "syntax",
    \ "spell",           "nospell",
    \ "spelllang"
    \ ]


function! s:startup()
    if has('nvim') && exists(':CocCommand')
       source $VIM_HOME/coc_config.vim
    endif
endfunction

autocmd VimEnter * call s:startup()

