---
name: free-disk
description: Free disk space with a deterministic script that loses no work. Use when the disk is full or low, or the user asks to clean up space, caches, or old/merged git worktrees.
---

# Free disk

The scripts decide what is safe; your job is to run them, then put the leftovers in front of the user.

1. Run `scripts/free-disk` (dry run). Done when you hold its report: what each step would free.
2. Run `scripts/free-disk --apply`. Done when it prints the final `== free:` line; report before → after.
3. Run `scripts/prune-worktrees` (dry run) and group its `keep` lines by reason. Report the groups that hold real disk: idle worktrees with `PR none`, `PR OPEN`, `detached HEAD`. Done when the user has named which groups to drop, or declined.
4. For each worktree the user names: `git -C <repo> stash push -u -m "free-disk: <name>"` when it has uncommitted changes, then `git -C <repo> worktree remove --force <literal path>`. A branch survives its worktree, so committed work stays reachable; a detached HEAD with commits on no branch needs `git branch keep/<name> HEAD` first.

## Reference

- **Measure with `df -h /` only.** `du` and `dust` count APFS clones (pnpm `node_modules`, app bundles) in full, so they report hundreds of GB that deleting would not free.
- **What counts as done, and what is never touched:** the header of `scripts/prune-worktrees` is the source of truth. `--closed` also drops closed-unmerged PRs; offer it, never default to it.
- **Leftovers** (`left for you to decide`): Docker volumes hold local databases; browser caches belong to running apps. Name them with sizes and let the user pick.
- **uv cache stays locked** while a long-running `uvx` tool (an MCP server) runs. The script gives up after a minute; tell the user to rerun once those sessions close. `uv cache prune --force` can break the running tool.
- **Config:** `PRUNE_WORKTREES_ROOTS` (colon-separated worktree folders, default `~/.herdr/worktrees`); `~/.config/prune-worktrees/protected` lists worktree names never removed.
- **Scheduling:** `free-disk --apply --if-below 40` runs only under 40 GiB free or when the last run is 20+ hours old, so a scheduler can call it hourly.
