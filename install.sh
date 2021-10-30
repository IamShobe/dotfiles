#!/usr/bin/env bash
export run_as=""
if [ -x "$(command -v sudo)" ]; then
  export run_as="sudo"
fi
set -e
if ! [ -x "$(command -v ansible)" ]; then
  eval $run_as apt update
  eval $run_as apt install ansible -y
fi
[[ ! -e ~/.dotfiles ]] && git clone https://github.com/IamShobe/dotfiles ~/.dotfiles
ansible-playbook -i ~/.dotfiles/hosts ~/.dotfiles/dotfiles.yml --ask-become-pass
if command -v terminal-notifier 1>/dev/null 2>&1; then
  terminal-notifier -title "dotfiles: Bootstrap complete" -message "Successfully set up dev environment."
fi
