---
name: chezmoi-helper
description: |
  Help users work with chezmoi, the dotfile manager for syncing configuration files across machines.
  Use this skill whenever the user mentions chezmoi, dotfiles, or wants to manage their configuration files.
  Covers workflows from initialization through advanced features like templating, encryption, password manager integration, and cross-machine setup.
  Also use this for troubleshooting chezmoi issues, understanding templates, or optimizing dotfile management.
---

# Chezmoi Helper

Chezmoi is a dotfile manager that lets users maintain configuration files across multiple machines with templating, encryption, and secret management. This skill helps users work with chezmoi at intermediate to advanced levels.

## Core Workflows

### Initialization & Setup
- `chezmoi init <repo-url>` - Initialize chezmoi with a dotfiles repo
- `chezmoi apply` - Apply managed dotfiles to the system
- `chezmoi status` - See which files differ from the repository
- `chezmoi update` - Pull changes from the repo and apply them

### File Management
- `chezmoi add <path>` - Add a file to chezmoi management
- `chezmoi edit <path>` - Edit a managed file in your editor
- `chezmoi remove <path>` - Stop managing a file
- `chezmoi diff` - Preview what changes would be applied
- `chezmoi verify` - Check that all files match their targets

### Advanced Operations
- `chezmoi merge` - Merge upstream changes (with conflict resolution)
- `chezmoi archive` - Create tarball/zip of managed files
- `chezmoi import` - Import files from tarballs/zips
- `chezmoi export` - Export managed files with templates preserved

## Templating System

Chezmoi uses Go text/template syntax with 70+ built-in functions. Templates are powerful for:
- **Machine-specific differences**: Use `{{ .hostname }}` or custom variables to vary configs by machine
- **Secret injection**: Integrate with password managers (1Password, Bitwarden, Vault, LastPass, KeePass, etc.)
- **Dynamic generation**: Build configs based on OS, architecture, or user-defined data
- **File operations**: Conditionally include/exclude files using template directives

### Template File Structure
Files in `~/.local/share/chezmoi/` (or `.chezmoi` directory in repo) can be templates:
- `filename.tmpl` → target is `filename` with template processing
- `.chezmoidata.yaml` → defines variables available to all templates
- `.chezmoidata/<machine>.yaml` → machine-specific data
- Use `{{ template "partial" . }}` to include template fragments

### Common Template Patterns
```
{{ if eq .hostname "work-laptop" }}
  # work-specific config
{{ else }}
  # personal config
{{ end }}

{{ with bitwarden "item-name" }}
  password: {{ .password }}
{{ end }}

{{ include "common-functions" }}
```

## Encryption & Secrets

### Setup Options
1. **Password Manager Integration** (recommended for teams)
   - `chezmoi completion` helps set up 1Password, Bitwarden, etc.
   - Secrets stored in vault, not in git repo

2. **File Encryption** (for repo-based secrets)
   - `age` (modern, no dependencies)
   - `gpg` (widely available)
   - `git-crypt` (transparent, git-integrated)

### Encrypting Files
- Add encrypted file: `chezmoi add --encrypt <path>`
- Edit encrypted file: `chezmoi edit-encrypted <path>`
- Encrypt specific patterns in `.chezmoiignore`

## Troubleshooting

### Common Issues

**Templates not rendering**
- Check `.chezmoidata.yaml` for variable definitions
- Verify template syntax: `{{ variable }}`
- Use `chezmoi execute-template` to test templates

**Files not applying**
- `chezmoi status` shows what differs
- `chezmoi diff` previews changes
- `chezmoi verify` checks current state
- Check permissions and target paths

**Merge conflicts**
- `chezmoi merge` guides you through conflicts
- Can manually resolve in `~/.local/share/chezmoi/`

**Encryption issues**
- Ensure GPG/age keys are configured
- Check `.chezmoiignore` for encryption patterns
- Verify password manager integration setup

## Machine-Specific Configuration

Use `.chezmoidata.yaml` to define variables:
```yaml
hostname: "{{ env "HOSTNAME" }}"
os: "{{ env "OSTYPE" }}"
email: "your@email.com"
```

Then reference in templates. For machine-specific data:
1. Create `.chezmoidata/[hostname].yaml`
2. Load in templates: `{{ include "chezmoidata/" .hostname ".yaml" }}`
3. Merge with base data in template logic

## Working with Multiple Machines

1. Initialize on new machine: `chezmoi init --apply <repo-url>`
2. Or use one-liner: `sh -c "$(curl -fsLS git.io/chezmoi)" -- init --apply <username>`
3. Update existing: `chezmoi update`
4. Push changes back: `cd ~/.local/share/chezmoi && git push`

## Helpful Commands

- `chezmoi data` - Show variables available to templates
- `chezmoi execute-template <file>` - Test template rendering
- `chezmoi managed` - List all managed files
- `chezmoi source-path <target>` - Show source file path
- `chezmoi cat <target>` - Display managed file contents
- `chezmoi help <command>` - Get help on any command

## When to Use This Skill

- Setting up chezmoi for the first time
- Configuring templates for machine-specific setups
- Integrating password managers or encryption
- Troubleshooting sync/apply issues
- Understanding chezmoi workflows and best practices
- Migrating existing dotfiles to chezmoi
- Setting up across multiple machines
