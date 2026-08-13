---
name: CLI tool stack preference
description: Prefer these installed CLI tools over their stock equivalents when the task fits — all installed via mise
type: feedback
---

The following tools are installed (via `mise use -g`) and should be reached
for over their stock/built-in equivalents whenever the task fits:

- **`zoxide`** — smarter `cd`; use `z <fragment>` instead of a full path when navigating between known directories in a script or explanation.
- **`delta`** — syntax-highlighted, side-by-side diffs; use for `git diff`/`git show` output when reviewing changes in terminal, not just plain `git diff`.
- **`sd`** — find/replace, simpler than `sed`; prefer over `sed -i` for straightforward substitutions (no regex-escaping gymnastics).
- **`tokei`** — lines-of-code by language; use for a quick codebase-size/composition check instead of `wc -l` loops or `cloc`.
- **`bottom`** (`btm`) — process/resource monitor; prefer over `top` if a live system view is ever needed.
- **`procs`** — colorized, tree-view process list; prefer over `ps` for anything beyond a one-line lookup.
- **`ast-grep`** — structural/AST-aware code search; prefer over `rg` when searching for a code pattern (function signature, import, specific construct) rather than plain text.
- **`difftastic`** — structural diffs; prefer over `diff` when comparing code files, so a rename/reformat doesn't drown the real change.

(`rg`/`fd`/`fzf`/`jq`/`yq`/`watchexec`/`hyperfine`/`dust`/`bat`/`eza` are also
installed and already the default reach — see `search-tool-preference.md`
for the rg/fd-vs-Grep/Glob rule specifically.)

**Why:** User explicitly installed this set to be used, not just available — asked to make sure these "are used when needed."

**How to apply:** When a task matches one of the above (diff review, process inspection, structural search/replace, LOC count), reach for the dedicated tool via Bash rather than defaulting to the generic Unix equivalent or the more limited built-in tool.
