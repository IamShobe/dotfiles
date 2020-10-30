GREP_OPTS='--color=auto --exclude-dir={.git,.hg,.svn}'
alias grep="grep $GREP_OPTS"
alias egrep="egrep $GREP_OPTS"
alias fgrep="fgrep $GREP_OPTS"
unset GREP_OPTS

alias ..='cd ..'
alias ...='cd ../..'

alias l='ls -l'
if [ "$(uname 2> /dev/null)" != "Linux" ]; then
    # macos
    alias ll='ls -a -l -G'
else
    # linux
    alias ls='ls --color=auto -N -F --group-directories-first'
    alias ll='ls -a -l -F'
fi


#alias dmesg='dmesg --color --reltime'

alias alf='autoload -Uz'
alias reload='source ~/.zshrc'

