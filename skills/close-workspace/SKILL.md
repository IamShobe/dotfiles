---
name: close-workspace
description: Close a Herdr workspace and remove the git worktrees its panes are in, losing no work. Use when the user asks to close, finish, or clean up a Herdr workspace.
---

# Close workspace

`scripts/close-workspace` decides what is safe; your job is to pick the target, show its plan, and run it. Requires `HERDR_ENV=1`.

1. Resolve the target. Done when you hold one workspace ID: the one the user named (ID or exact label from `herdr workspace list`), or `$HERDR_WORKSPACE_ID` when they said "this workspace".
2. Run `scripts/close-workspace <id>` (dry run) and show the user its plan.
3. Run `scripts/close-workspace <id> --apply` once the plan holds no surprise: every agent `idle` or `done`, and nothing listed that the user did not expect. An agent `working` or `blocked`, or a worktree you cannot account for, goes to the user first. Done when every `worktree` line from the plan has a `removed` or `keep` outcome.
4. Report what was removed, and every `stashed` / `branched` line with how to get it back: `git -C <repo> stash list` then `git stash pop`, or `git checkout keep/<folder>`.

When the target is the caller's own workspace, the script closes it last; this session ends with it, so report the plan before step 3.
