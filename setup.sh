function base_requirements {
	sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \
			libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev \
			libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python-openssl \
			git apt-transport-https ca-certificates curl \
			gnupg-agent software-properties-common python3-pip vim
	sudo apt-get update
}

function install_zsh {
	 sudo apt-get install -y zsh
	 sudo chsh -s /bin/zsh $USER
}

function install_docker {
	curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
	sudo add-apt-repository \
			   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
			      $(lsb_release -cs) \
				     stable"
	sudo apt-get update
	sudo apt-get install -y docker-ce docker-ce-cli containerd.io
	sudo usermod -aG docker $USER
}

function install_fast_installer {
	sudo apt install -y python3-pip
	pip3 install fast-installer
}

function install_dotfiles {
	install_fast_installer
	[[ ! -e ~/.dotfiles ]] && git clone https://github.com/IamShobe/dotfiles ~/.dotfiles
	cd ~/.dotfiles
	fastinstall -af
}


export PATH=$PATH:$HOME/.local/bin

base_requirements
install_zsh
install_docker
install_dotfiles

exec /bin/zsh  # rerun with zsh 
pyenv install 3.9.1 
pyenv install 2.7.18
pyenv global 3.9.1 2.7.18  # set 3.9 as default and 2.7 as secondary
nvm install --lts

