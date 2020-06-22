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

source ~/.vim/airline.vim
source ~/.vim/autocomplete.vim
let g:gitgutter_preview_win_floating = 1
let g:gitgutter_highlight_linenrs = 1
let g:gitgutter_preview_win_floating = 1
set updatetime=100  " for updating file status

"let g:solarized_termcolors=256

"let background=dark
colorscheme molokai
let g:molokai_original = 1
let g:rehash256 = 1
let g:python_highlight_all = 1
syntax enable


source ~/.vim/shortcuts.vim

