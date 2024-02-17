function! AirlineTabsFormat(et, ts, sw)
    if &et
        return "spaces " . &ts . ":" . &sw
    else
        return "tab"
    endif
endfunction

let g:airline_theme='deus'
let g:airline_powerline_fonts = 1
let g:airline#extensions#whitespace#enabled = 1
let g:airline#extensions#whitespace#mixed_indent_algo = 1
let g:airline#extensions#tabline#enabled = 1
let g:airline#extensions#tabline#formatter = 'default'
let g:airline_section_z = airline#section#create(['%{AirlineTabsFormat(&expandtab, &tabstop, &shiftwidth)}',' %3p%% ',g:airline_symbols.linenr,'%3l:%c'])

