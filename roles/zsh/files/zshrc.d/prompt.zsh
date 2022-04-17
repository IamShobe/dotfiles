# Misc prompts
ZCALCPROMPT='%F{48}%1v>%f '
SPROMPT='zsh: correct '%F{166}%R%f' to '%F{76}%r%f' [nyae]? '

autoload -Uz colors && colors

function middle_prompt {
    # overrideable function
}

PROMPT=''
PROMPT+='$(virtualenv_prompt_info)'  # venv
PROMPT+='%(!.%{$fg[red]%}.%{$fg[green]%})%n'  # user
PROMPT+='%{$fg[yellow]%}@%{$fg[blue]%}%M%f '  # domain
PROMPT+='$(middle_prompt)'
PROMPT+='%{$fg[magenta]%}%(6~|%-1~/…/%4~|%5~)%f' # path
# PROMPT+='$fg[magenta]%~%f' # path full
PROMPT+=$'\n'
PROMPT+='$GITSTATUS_PROMPT'
#PROMPT+=$'\n'
#PROMPT+='$(gitprompt)'  # git
PROMPT+='%(?..%K{9}%F{15})%(!.#.%%)%k%f ' # endsign

KUBE_PS1_SYMBOL_ENABLE=false
RPROMPT='$(kube_ps1)'
# RPROMPT='$GITSTATUS_PROMPT'

PS2='%F{14}%_%F{15}>%f '

VIRTUAL_ENV_DISABLE_PROMPT=1

# ZSH_GIT_PROMPT_FORCE_BLANK=1
# ZSH_GIT_PROMPT_SHOW_STASH=1
ZSH_GIT_PROMPT_NO_ASYNC=1
ZSH_GIT_PROMPT_ENABLE_SECONDARY=1
ZSH_GIT_PROMPT_SHOW_UPSTREAM="symbol"

# ZSH_THEME_GIT_PROMPT_PREFIX=" %{$fg_bold[default]%}≺ "
#ZSH_THEME_GIT_PROMPT_PREFIX=" · "
# ZSH_THEME_GIT_PROMPT_PREFIX=""
# ZSH_THEME_GIT_PROMPT_SUFFIX="›"
# ZSH_THEME_GIT_PROMPT_SEPARATOR="‹"
# ZSH_THEME_GIT_PROMPT_BRANCH="⎇ %{$fg_bold[cyan]%}"
# ZSH_THEME_GIT_PROMPT_UPSTREAM_SYMBOL="%{$fg_bold[yellow]%}⟳ "
# ZSH_THEME_GIT_PROMPT_UPSTREAM_PREFIX="%{$fg[red]%}(%{$fg[yellow]%}"
# ZSH_THEME_GIT_PROMPT_UPSTREAM_SUFFIX="%{$fg[red]%})"
# ZSH_THEME_GIT_PROMPT_DETACHED="@%{$fg_no_bold[cyan]%}"
# ZSH_THEME_GIT_PROMPT_BEHIND="%{$fg_no_bold[blue]%}↓"
# ZSH_THEME_GIT_PROMPT_AHEAD="%{$fg_no_bold[blue]%}↑"
# ZSH_THEME_GIT_PROMPT_UNMERGED="%{$fg[red]%}✖"
# ZSH_THEME_GIT_PROMPT_STAGED="%{$fg[green]%}●"
# ZSH_THEME_GIT_PROMPT_UNSTAGED="%{$fg[red]%}✚"
# ZSH_THEME_GIT_PROMPT_UNTRACKED="…"
# ZSH_THEME_GIT_PROMPT_STASHED="%{$fg[blue]%}⚑"
# ZSH_THEME_GIT_PROMPT_CLEAN="%{$fg_bold[green]%}✔"
# ZSH_THEME_GIT_PROMPT_TAGS_PREFIX=" · 🏷 "

# Main prompt
autoload -Uz add-zsh-hook


setup() {
    [[ -n $_PROMPT_INITIALIZED ]] && return
    _PROMPT_INITIALIZED=1
    

    function _prompt_update_user() {
    
        integer _prompt_next_command _prompt_last_command

        function _prompt_preexec() {
            (( _prompt_next_command++ ))
        }
        add-zsh-hook preexec _prompt_preexec
    
        if (( _prompt_next_command == _prompt_last_command )); then
            last_was_empty=1
        else
            last_was_empty=0
            (( _prompt_last_command = _prompt_next_command ))
        fi
    }
    
    add-zsh-hook precmd _prompt_update_user
    
    function fzf-redraw-prompt() {
        local precmd
        for precmd in ${precmd_functions:#_prompt_newline}; do
            $precmd
        done
        zle reset-prompt
    }
    zle -N fzf-redraw-prompt
}
setup
