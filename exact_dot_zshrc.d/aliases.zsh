GREP_OPTS='--color=auto'
alias grep="grep $GREP_OPTS"
alias egrep="egrep $GREP_OPTS"
alias fgrep="fgrep $GREP_OPTS"
unset GREP_OPTS

alias ..='cd ..'
alias ...='cd ../..'

if command -v exa 2>&1 >/dev/null; then 
    alias l='exa -l'
    alias ls='exa -F --group-directories-first'
    alias ll='ls -a -l --time-style=long-iso --git'
else
    alias ls='ls --color'
    alias l='ls -l'
    alias ll='ls -alF'
fi

if command -v nvim 2>&1 >/dev/null; then
   ovim=`which vim`
   alias ovim=$ovim

   function vim() {
      if [ $# -eq 0 ]; then
        nvim
        return
      fi

      # Added "--hardlink=false" option to get neovim undo available.
      chezmoi verify $1 > /dev/null 2>&1 && chezmoi edit --watch --hardlink=false $1 || nvim $@
    }
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

alias debug_trach="zsh -l --sourcetrace"
alias debug_startup_time="time ZSH_DEBUGRC=1 zsh -i -c exit"
