GREP_OPTS='--color=auto --exclude-dir={.git,.hg,.svn}'
alias grep="grep $GREP_OPTS"
alias egrep="egrep $GREP_OPTS"
alias fgrep="fgrep $GREP_OPTS"
unset GREP_OPTS

alias ..='cd ..'
alias ...='cd ../..'

alias l='ls -l'
alias ll='ls -a -l'
alias ls='ls -G'

#alias ls='ls --color=auto -N -F --group-directories-first'

#alias dmesg='dmesg --color --reltime'

alias alf='autoload -Uz'
