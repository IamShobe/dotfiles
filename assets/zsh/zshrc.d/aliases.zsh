GREP_OPTS='--color=auto --exclude-dir={.git,.hg,.svn}'
alias grep="grep $GREP_OPTS"
alias egrep="egrep $GREP_OPTS"
alias fgrep="fgrep $GREP_OPTS"
unset GREP_OPTS

alias ..='cd ..'
alias ...='cd ../..'

if command -v exa; then 
    alias l='exa -l'
    alias ls='exa --icons -F --group-directories-first'
    alias ll='ls -a -l --time-style=long-iso --git'
fi


#alias dmesg='dmesg --color --reltime'

alias alf='autoload -Uz'
alias reload='source ~/.zshrc'
alias edit_rc='vim ~/.zshrc'
alias edit_aliases="editor ${ZSH_DIR}/aliases.zsh"

if command -v bat; then
    alias cat='bat'
fi
if command -v fd; then
    alias find='fd'
fi

if command -v tmux; then
    #alias rtmux="tmux"
    alias rtmux="tmux attach -t base || tmux new -s base"
fi

