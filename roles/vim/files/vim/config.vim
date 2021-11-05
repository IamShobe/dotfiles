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

if !isdirectory($VIM_HOME."/swapfiles/")
    call mkdir($VIM_HOME."/swapfiles/", "", 0700)
endif

set directory=$VIM_HOME/swapfiles/

if !isdirectory($VIM_HOME."/undodir/")
    call mkdir($VIM_HOME."/undodir/", "", 0700)
endif
set undodir=$VIM_HOME/undodir/
set undofile

if !exists('g:airline_symbols')
    let g:airline_symbols = {} 
endif
 
source $VIM_HOME/airline.vim
source $VIM_HOME/autocomplete.vim
let g:gitgutter_preview_win_floating = 1
let g:gitgutter_highlight_linenrs = 1
let g:gitgutter_preview_win_floating = 1
set updatetime=100  " for updating file status

let g:NERDDefaultAlign = 'left'
let g:NERDCompactSexyComs = 1
let g:NERDSpaceDelims = 1
let g:NERDCommentEmptyLines = 1


"let g:solarized_termcolors=256

"let background=dark

try
  colorscheme molokai
catch /^Vim\%((\a\+)\)\=:E185/

        " deal with it
        "
endtry

let g:molokai_original = 1
let g:rehash256 = 1
let g:python_highlight_all = 1
syntax enable


source $VIM_HOME/shortcuts.vim

let g:ycm_confirm_extra_conf = 0



