#!/usr/bin/env bash
export run_as=""
if [ -x "$(command -v sudo)" ]; then
    export run_as="sudo"
fi
unameOut="$(uname -s)"
case "${unameOut}" in
    Linux*)     machine=Linux;;
    Darwin*)    machine=Mac;;
    CYGWIN*)    machine=Cygwin;;
    MINGW*)     machine=MinGw;;
    *)          machine="UNKNOWN:${unameOut}"
esac

if [ $machine = Mac ]; then
    echo "Detected macos machine!"
    if ! [ -x "$(command -v brew)" ]; then
        echo "brew was not detected in machine.. installing..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        echo "brew was detected!"
        # required for realpath
        brew install coreutils noti
    fi

elif [ $machine = Linux ]; then
    echo "Detected linux based machine!"
    if ! [ -x "$(command -v apt)" ]; then
        echo "Currently only debian based distros are supported!"
        exit 1
    fi
    if ! [ -x "$(command -v ansible)" ]; then
      eval $run_as apt-get update
    fi
fi
pip3 install pipx
pipx install ansible --include-deps
set -e
[[ ! -e ~/.dotfiles ]] && git clone https://github.com/IamShobe/dotfiles ~/.dotfiles
export PATH=$HOME/.local/bin:$PATH
ansible-playbook -i ~/.dotfiles/hosts ~/.dotfiles/dotfiles.yml --ask-become-pass $@

if command -v terminal-notifier 1>/dev/null 2>&1; then
  terminal-notifier -title "dotfiles: Bootstrap complete" -message "Successfully set up environment."
elif command -v noti 1>/dev/null 2>&1; then
  noti -t "dotfiles: Bootstrap complete" -m "Successfully set up environment."
fi

end_message() {
    echo '# Installation finished successfully!!!'
    echo '## Configure python global versions using:'
    echo '- `pyenv versions` # list installed versions'
    echo '- `pyenv global <version> [<version>]` # configure multiple versions as global'
    echo '## Configure node global versions using:'
    echo '- `nvm ls` # list versions available'
    echo '- `nvm alias default <version>` # configure default node version globally'
}

end_message | gum format
