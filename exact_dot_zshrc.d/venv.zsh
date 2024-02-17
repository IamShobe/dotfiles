# Virtualenvwrapper things
export WORKON_HOME=$HOME/.virtualenvs
export PROJECT_HOME=$HOME/Devel
[ -f $HOME/.local/bin/virtualenvwrapper.sh ] && source $HOME/.local/bin/virtualenvwrapper.sh
[ -f /usr/local/bin/virtualenvwrapper.sh ] && source /usr/local/bin/virtualenvwrapper.sh


function virtualenv_prompt_info(){
  [[ -n ${VIRTUAL_ENV} ]] || return
  echo "${ZSH_THEME_VIRTUALENV_PREFIX:=[}${VIRTUAL_ENV:t}${ZSH_THEME_VIRTUALENV_SUFFIX:=]} "
}


