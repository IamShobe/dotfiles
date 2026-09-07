---
name: claude-local-gateway
description: Local gateway configuration is machine-local; public dotfiles contain only generic shell integration.
metadata:
  type: project
---

The user uses a local Bifrost gateway with Claude Code. Provider endpoints, model identifiers, credentials, runtime databases, and backups must stay outside the public dotfiles repository. Only generic shell integration belongs in chezmoi. Subscription authentication stays owned by Claude Code; do not copy refresh tokens into gateway configuration.

**Why:** Keep private provider configuration out of public dotfiles.
**How to apply:** Inspect the current wrapper and machine-local configuration before making changes. Disable chezmoi automatic commits and pushes per operation unless publishing was explicitly requested. Related: [[chezmoi-claude-settings-template]].
