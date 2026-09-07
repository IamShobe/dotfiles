---
name: claude-litellm-gateway
description: `claude` is a zsh wrapper that routes through a local LiteLLM gateway (:4000) — Claude models pass through to Anthropic on the subscription; extra (work) models come from an unmanaged machine-local file
metadata:
  type: project
---

Set up 2026-09-07. `claude` in zsh is a function (`~/.zshrc.d/claude-litellm.zsh`) that lazily
starts LiteLLM on 127.0.0.1:4000 and sets `ANTHROPIC_BASE_URL` + `ANTHROPIC_CUSTOM_HEADERS`
(`x-litellm-api-key`). Generic config in dotfiles: `~/.config/litellm/config.yaml` — `anthropic/*`
wildcard forwards Claude Code's own OAuth (official LiteLLM "Claude Code Max" flow) and
`include`s `models.local.yaml`. Workplace models (Azure Foundry via an APIM Responses-API router,
Entra token from `az login`) live ONLY in `~/.config/litellm/models.local.yaml` and in the
`modelPicker` key of `~/.claude/settings.json` — both machine-local, never in the dotfiles repo
(it's public). `modelPicker` is in the settings template's LOCAL_ONLY_KEYS for that reason.

**Why:** one command, per-model routing, subscription untouched; employer-specific endpoints
must not leak into public dotfiles.

**How to apply:** `claude-proxy {status|stop|restart|logs}`; `CLAUDE_DIRECT=1 claude` bypasses the
gateway. Azure 401 → `az login`. Use `[1m]` suffix on 1M-window models. Workplace model names /
URLs go in models.local.yaml, never config.yaml. User avoids Chinese-origin models/tools.
Related: [[chezmoi-claude-settings-template]].
