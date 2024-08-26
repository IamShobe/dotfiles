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
    echo "🔄 Updating dotfiles"
    chezmoi update
    echo "✅ Dotfiles updated"
    echo "If you want to fully update repo deps use: chezmoi apply -R"
}


dotfiles_check_updates() {
    chezmoi git remote update > /dev/null 
    UPSTREAM=${1:-'@{u}'}
    LOCAL=$(chezmoi git rev-parse @)
    REMOTE=$(chezmoi git rev-parse "$UPSTREAM")
    BASE=$(chezmoi git merge-base @ "$UPSTREAM")

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

