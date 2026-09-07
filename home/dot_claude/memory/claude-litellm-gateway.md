---
name: claude-litellm-gateway
description: `claude` is a zsh wrapper that routes through a local LiteLLM gateway (:4000) — Claude models pass through to Anthropic on the subscription, Azure Foundry models (astra, gpt-5.6-*) go to the work APIM router
metadata:
  type: project
---

Set up 2026-09-07. `claude` in zsh is a function (`~/.zshrc.d/claude-litellm.zsh`) that lazily
starts LiteLLM on 127.0.0.1:4000 and sets `ANTHROPIC_BASE_URL` + `ANTHROPIC_CUSTOM_HEADERS`
(`x-litellm-api-key`). Config: `~/.config/litellm/config.yaml` — `anthropic/*` wildcard forwards
Claude Code's own OAuth (official LiteLLM "Claude Code Max" flow); `astra`, `gpt-5.6-sol/terra/luna`,
`gpt-5.5` are `azure/responses/<slug>` against the work APIM router with `api_version: preview` and
`azure_scope: management.azure.com` (token auto-minted from `az login`). `modelPicker` rows in
`~/.claude/settings.json` (chezmoi `modify_settings.json.tmpl`) expose them in `/model`.

**Why:** one command, per-model routing, subscription untouched; APIM router is Responses-API-only
and validates ARM-audience tokens.

**How to apply:** `claude-proxy {status|stop|restart|logs}`; `CLAUDE_DIRECT=1 claude` bypasses the
gateway. If Azure models fail with 401 → `az login`. Use `--model 'astra[1m]'` (the `[1m]` tells
Claude Code the 1M window). Don't add Chinese-origin models/tools (user preference). All files live
in the chezmoi source — edit there, then `chezmoi apply`. Related: [[chezmoi-claude-settings-template]].
