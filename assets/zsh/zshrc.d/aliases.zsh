GREP_OPTS='--color=auto --exclude-dir={.git,.hg,.svn}'
alias grep="grep $GREP_OPTS"
alias egrep="egrep $GREP_OPTS"
alias fgrep="fgrep $GREP_OPTS"
unset GREP_OPTS

alias ..='cd ..'
alias ...='cd ../..'

alias l='exa -l'
alias ls='exa --icons -F --group-directories-first'
alias ll='ls -a -l'


#alias dmesg='dmesg --color --reltime'

alias alf='autoload -Uz'
alias reload='source ~/.zshrc'
alias edit_rc='vim ~/.zshrc'
alias edit_aliases="editor ${ZSH_DIR}/aliases.zsh"

alias cat='bat'
alias find='fd'
