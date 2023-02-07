autocmd StdinReadPre * let s:std_in=1
autocmd VimEnter * if argc() == 1 && !exists("s:std_in") | silent! lcd %:p:h | NvimTreeToggle | endif
