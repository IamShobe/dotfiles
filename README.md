DOTFILES
========

## How to start?
Bootstrap:
```bash
curl https://raw.githubusercontent.com/IamShobe/dotfiles/main/bootstrap.sh | bash
```

OR:

```bash
chezmoi init IamShobe --apply
```

## To update
```bash
chezmoi update
```

## Daily commands - for using chezmoi
```bash
chezmoi add $FILE # adds $FILE from your home directory to the source directory.
chezmoi edit $FILE # opens your editor with the file in the source directory that corresponds to $FILE.
chezmoi status # gives a quick summary of what files would change if you ran chezmoi apply.
chezmoi diff # shows the changes that chezmoi apply would make to your home directory.
chezmoi apply # updates your dotfiles from the source directory.
chezmoi edit --apply $FILE # is like chezmoi edit $FILE but also runs chezmoi apply $FILE afterwards.
chezmoi cd # opens a subshell in the source directory.
```

## Update global devbox package
```bash
devbox global add <package>
chezmoi re-add ~/.local/share/devbox/  # refresh it to sync with the rest
```

