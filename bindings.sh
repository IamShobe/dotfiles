#!/bin/sh

DOTFILES_UPDATE_PROMPT="🆕"

dotfiles_prompt() {
     STATUS=$(dotfiles_check_updates)
     if [ "$STATUS" = "Need to pull" ]; then
        echo " $DOTFILES_UPDATE_PROMPT"
     else
        echo ""
     fi
}

dotfiles_update() {
    dotfiles_check_updates
    set -e
    cd ~/.dotfiles 
    git pull
    ./install.sh
}


dotfiles_check_updates() {
    cd ~/.dotfiles
    git remote update > /dev/null
    UPSTREAM=${1:-'@{u}'}
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse "$UPSTREAM")
    BASE=$(git merge-base @ "$UPSTREAM")

    if [ $LOCAL = $REMOTE ]; then
        echo "Up-to-date"
    elif [ $LOCAL = $BASE ]; then
        echo "Need to pull"
    elif [ $REMOTE = $BASE ]; then
        echo "Need to push"
    else
        echo "Diverged"
    fi
}

