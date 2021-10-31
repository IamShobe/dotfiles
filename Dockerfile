FROM ubuntu:20.04
RUN apt update && apt install -y curl git
RUN curl https://raw.githubusercontent.com/IamShobe/dotfiles/master/install.sh | bash
CMD /bin/zsh

