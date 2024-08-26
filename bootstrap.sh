#!/bin/sh

# Install devbox
curl -fsSL https://get.jetify.com/devbox | bash

# Adds global chezmoi
devbox global add chezmoi
