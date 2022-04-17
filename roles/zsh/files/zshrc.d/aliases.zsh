GREP_OPTS='--color=auto --exclude-dir={.git,.hg,.svn}'
alias grep="grep $GREP_OPTS"
alias egrep="egrep $GREP_OPTS"
alias fgrep="fgrep $GREP_OPTS"
unset GREP_OPTS

alias ..='cd ..'
alias ...='cd ../..'

if command -v exa 2>&1 >/dev/null; then 
    alias l='exa -l'
    alias ls='exa --icons -F --group-directories-first'
    alias ll='ls -a -l --time-style=long-iso --git'
else
    alias ls='ls --color'
    alias l='ls -l'
    alias ll='ls -alF'
fi

if command -v nvim 2>&1 >/dev/null; then
   ovim=`which vim`
   alias ovim=$ovim
   alias vim='nvim'
fi


#alias dmesg='dmesg --color --reltime'

alias alf='autoload -Uz'
alias reload='source ~/.zshrc'
alias edit_rc='vim ~/.zshrc'
alias edit_aliases="editor ${ZSH_DIR}/aliases.zsh"

if command -v bat 2>&1 >/dev/null; then
    alias cat='bat'
fi
#if command -v fd 2>&1 >/dev/null; then
#    alias find='fd'
#fi

if command -v tmux 2>&1 >/dev/null; then
    #alias rtmux="tmux"
    alias rtmux="tmux attach -t base || tmux new -s base"
fi

