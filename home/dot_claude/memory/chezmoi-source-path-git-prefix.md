---
name: chezmoi-source-path-git-prefix
description: "chezmoi source-path already resolves inside home/ — cd there and prefix paths with home/ again, and every git command 404s."
metadata:
  node_type: memory
  type: project
  originSessionId: current
  modified: 2026-08-13T19:42:38.376Z
---

`chezmoi source-path` (with or without a target arg) returns a path already
inside the repo's `home/` subdirectory — e.g. `~/.local/share/chezmoi/home`
for the bare form, or `~/.local/share/chezmoi/home/dot_claude/CLAUDE.md` for
a target. But the git repo root for the dotfiles repo (`IamShobe/dotfiles`)
is one level *above* that, at `~/.local/share/chezmoi` itself.

**The mistake:** `cd "$(chezmoi source-path)"` lands inside `home/`. From
there, running `git add home/dot_claude/foo` or `git diff -- home/...`
double-prefixes the path — it doesn't exist relative to that cwd, and git
fails with "did not match any files" / "could not open directory".

**Why it's easy to hit:** `chezmoi diff`/earlier output in the same session
often prints paths *with* the `home/` prefix (since that's the repo-relative
path from the actual git root), which primes the wrong path to reach for
once you've already `cd`'d one level deeper into `home/`.

**How to apply:** After `cd "$(chezmoi source-path)"`, git paths are
relative to `home/` already — drop the `home/` prefix (e.g.
`git add dot_claude/CLAUDE.md`, not `git add home/dot_claude/CLAUDE.md`).
If a `home/`-prefixed path is already in hand (e.g. copied from a `chezmoi
diff` line), either strip the prefix, or `cd` to the actual git root
(`chezmoi source-path` minus the trailing `/home`, or just
`dirname "$(chezmoi source-path)"`) and keep the `home/` prefix intact.
Don't mix the two conventions in one command chain.
