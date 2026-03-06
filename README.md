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

## Manage tools with mise
```bash
mise add <tool>[@version]  # add a new tool
mise remove <tool>         # remove a tool
mise install               # install all tools in .mise.toml
mise ls installed          # list installed tools
```

Edit `~/.mise.toml` to add/remove tools, then run `mise install` to sync.

