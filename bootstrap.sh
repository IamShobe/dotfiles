#!/bin/sh
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

set -e

ensure_brew_package ()
{
  BINARY=$1
  PACKAGE=$2

  if ! [ -x "$(command -v $BINARY)" ]; then
    echo "Command $BINARY not found attempting to install it"
    brew install $PACKAGE
  fi
}


ensure_apt_package ()
{
  BINARY=$1
  PACKAGE=$2

  if ! [ -x "$(command -v $BINARY)" ]; then
    echo "Command $BINARY not found attempting to install it"
    apt install -y $PACKAGE
  fi
}


if [ $machine = Mac ]; then
    echo "Detected macos machine!"
    if ! [ -x "$(command -v brew)" ]; then
        echo "brew was not detected in machine.. installing..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        echo "brew was detected!"
        # required for realpath
        # brew install coreutils noti

        ensure_brew_package git git
    fi

elif [ $machine = Linux ]; then
    echo "Detected linux based machine!"
    if ! [ -x "$(command -v apt)" ]; then
        echo "Currently only debian based distros are supported!"
        exit 1
    fi


    apt update
    ensure_apt_package xz xz-utils
    ensure_apt_package git git
fi

sh -c "$(curl -fsLS get.chezmoi.io)" -- -b $HOME/.local/bin init --apply IamShobe

