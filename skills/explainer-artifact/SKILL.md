---
name: explainer-artifact
description: Write a human-facing "explainer" artifact that summarizes a change, feature, refactor, migration or incident — for teammates and reviewers, not machines. Heavy on visuals, TLDR-first, no reading fatigue. Covers what changed, what was deprecated, and which interfaces changed (user-facing AND developer-facing). Starts from a diff, PRs, a ticket or a Slack thread. Use when the user says "create a summary artifact", "explain what changed", "write up this feature/PR/refactor/incident", "make a doc for the team", or asks to document a change visually.
allowed-tools: Read, Edit, Write, Bash, Grep, Glob, Skill, Agent, Artifact, AskUserQuestion
compatibility: Needs Node 18+, pnpm or npm, python3, uv, gh and git. Builds on the web-artifacts-builder skill (which uses diagram-design), installed by skillshare or the iamshobe marketplace; scripts/explainer.py finds it.
metadata:
  requires: "web-artifacts-builder diagram-design"
  requires-sources: "IamShobe/dotfiles cathrynlavery/diagram-design"
---

# Explainer Artifact

A one-page, visual explainer of a change or an incident for people who weren't there. A reader gets *what happened, why it matters and what to do* in under two minutes of scanning.

This skill owns the **story** (structure, formatting, content). `web-artifacts-builder` (`$WAB`) owns the mechanics (kit, theme, diagrams, build, verify). `S` = this skill's directory; `X` = `$S/scripts/explainer.py` (run it directly; `uv` handles its dependencies).

## Fewest turns

The cost is agent round-trips, not builds. A first publish takes **3 turns**; each later edit takes **1**.

| Turn | What you send (one response, calls run in order) |
|---|---|
| 1 | `X start --name <name> [inputs]`: paths, every rule file, PR and deploy status, ticket links, git facts with the code diff, and the App.tsx scaffold |
| 2 | `Write` App.tsx (a new file) + `Write` specs.json + `Bash X build <name>` + `Read` the contact sheet + `Artifact` publish (private, so a first draft is fine) |
| 3 | `Bash X url <name> <url>` + any fixes as `Edit`s + `X build <name>` + publish again; then the reply with the share message |
| edit | `Edit` App.tsx + `X build <name>` + `Artifact` publish (with `url` from explainer.json) |

- `start` prints the code diff when it's under ~900 lines (tests and generated files left out). Read source files only when it says the diff is too big, or for a *why* the diff and PR don't show; then add those reads to turn 2 before the `Write`.
- Fetch a ticket or thread only when the PR doesn't explain the why; send the fetch in turn 1 alongside `start` when you already know it's needed.
- Never `Read` the rule files: `start` printed them. Never re-read a file you wrote.
- Change App.tsx only with `Edit`, never `sed`: a shell edit forces a re-read before the next `Edit`.
- `verify.sh` checks only literal values: write `<Src path="…">` and ticket links inline, never through a constant.
- `start` prints absolute paths; every shell is fresh, so use them.
- Text-only edits: skip the contact sheet. Open it only when layout changed.
- Status moved? `X refresh <name>` re-checks PRs and deploys, rebuilds and lists the prose to update.
- A later session: `X list` finds the workspace and URL; `Read` its App.tsx once, then edit turns as above.
- Ask the user nothing before the first publish. They prune afterwards.

## Inputs

Every input is a flag of `X start`, repeatable, all optional:

| Input | Flag | What `start` does |
|---|---|---|
| A git range | `[base] [head]`, `--path <dir>` | facts: commits, files, interface lines, link ranges, migrations |
| A PR | `--pr 123` / `owner/repo#123` / URL | merged or open, merge SHA, and with one PR of this repo, the git range |
| Deploy state | per repo in `EXPLAINERS_CONFIG` (`~/.config/explainers/config.json`), or `--deploy-check '<cmd {sha}>'` for one run | runs it per merged PR: exit 0 deployed, 1 not yet |
| A ticket | `--ticket ID` / URL; ids in PR titles are found automatically | GitHub issues: fetched inline. Others: the link (the repo's `ticket_url` in the config) and the fetch to use if needed |
| A Slack thread | `--thread <url>` | the exact `slack_read_thread` call to send |
| The page kind | `--kind change` (default) / `incident` | which sections the scaffold starts with |

No PR given: the current branch's PR is used. Not in a repo: the story comes from the inputs alone.

## The workspace

`EXPLAINERS_DIR/<name>/` (default `~/.local/share/explainers`) keeps everything: `App.tsx`, `specs.json`, `status.ts`, `explainer.json` (inputs and the published URL), the build and `<name>.html`. Nothing lives in a scratchpad, so any later session can edit the same page and keep its URL.

The scaffold is a starting point, not a form: every slot is a `⟨…⟩` placeholder (verify fails until each is filled or cut). Rename, reorder, merge or cut sections; swap any block; add diagrams, a `<TimeChart>` or a `<Playground>` where the story is better told that way. The PR status parts (eyebrow, TL;DR status row, rollout steps) read `status.ts`, so `refresh` keeps them true.

## Non-negotiables

1. **Readability is the core standard** (`references/readability.md`): outcome first, takeaways ≤ 25 words, paragraphs ≤ 60, numbers not adjectives, lists ≤ 5, one word per concept, no filler, end on one action.
2. **TL;DR first**: a `<Tldr>` (what broke or changed, why, fix, status, what you do) and the main `<BeforeAfter>`, in plain words. Then the long version.
3. **Glance test** (`references/formatting.md`): each block makes its point to a reader who reads none of its sentences. One example, values not sentences, outcome first, why last.
4. **Introduce before you use**: every new word gets `<Term def>` at its first appearance, before any heading, diagram or table uses it.
5. **Real examples, honest status**: identifiers, code and names from the change, verified against source. Every ticket and PR is a `<Ref>` link, every code mention a `<Src>`. Merged is not deployed.

## Story

- **One arc.** Change: context → what was missing → the core shift → how it works → what changes for the reader → what to do. Incident: impact → timeline → cause → fix → rollout → follow-ups.
- **3–4 parts** with `group`, section titles ≤ 4 words.
- **One running example** (a person, a request, a row) through the whole page, diagrams included.
- **A smart outsider**: knows the product, not this code.
- **Takeaway test**: the thesis plus each `takeaway`, read in order, is one coherent paragraph (`verify.sh` prints it). If not, reorder or cut.

| Section | Kit |
|---|---|
| Hero: eyebrow with `<Ref>` links and status, title, thesis | `<Page eyebrow title thesis pills>` |
| TL;DR | `<Tldr>` + `<BeforeAfter example rows result>` |
| What changed for users (if any) | `<BeforeAfter>`, a mockup |
| How it works / why it broke | one diagram in `<Figure>` |
| What happened (incident) | a timeline: `<Table>` When · What, or a `<TimeChart>` with milestones |
| Interface changes | `<Changes>`, user-facing and developer-facing apart |
| Deprecated & removed | `<Deprecations>` |
| Rollout status | `<Steps>` from `status.ts`, plus what happens after deploy |
| How to check it | `<Code>`: the one command, query or URL that proves it |
| Risk and rollback | `<Table>` If · You see · Undo, only real risks |
| Decisions needed | `<Table>` Question · Who · By, only when something is open |

## Diagrams (≤ 3)

Pick each type from `diagram-types.md` (printed by `start`) by the question its section answers: a request path is a `sequence`, a status change a `state`, a migration a `db-schema`, a rollout a `gantt`. Never mermaid or hand-rolled boxes.

- **⚙ rendered types**: the workspace's `specs.json` array; `X build` renders it. A rejected spec says what to fix; change the spec, never the output.
- **✎ hand-drawn types**: one background subagent, started in turn 2. Import names are predictable (`auth-flow` → `import { AuthFlow } from '@/diagrams/auth-flow'`), so write `App.tsx` meanwhile. Prompt:

> Draw these diagrams for an explainer page. No questions, no extra files. Read `$WAB/references/diagram-brief.md`, then for each diagram only `$DIAGRAM_DESIGN/references/type-<type>.md`. Plans: `<slug · type · question>`. Vocabulary: `<terms>`. Write each to `<workspace>/<slug>.html` containing only the `<svg>`. From `<workspace>`, run `bash $WAB/scripts/diagram-to-jsx.sh <name> <files>`; fix a rejected file once. Never edit the generated .tsx. Reply with only the import lines.

## Build and publish

`X build <name>` bundles and runs `verify.sh`: placeholders left, story (takeaway paragraph, term order, jargon), `<Src>` links at a pushed SHA, theme and style, overflow and tiny text at 3 widths, readability ⚠, and one light+dark contact sheet. Fix everything in one pass.

Publish the `<name>.html` path it prints (never `bundle.html`) with a one-sentence `description`; pass `url` when the workspace has one. Then stop and let the user prune.

## The message to share

The reply after publishing ends with a message the user can paste into Slack as it is. Write it the way a teammate would: 2–4 short sentences in plain words, first person, no headings, bullets, emoji or labels ("TL;DR:", "Status:"). Say what happened and what it means for the reader, where it stands, the one ask (or that there is nothing to do), then the link.

> I wrote up why checkout cancelled 312 orders since Mar 3: it only ever tried the first saved card. The fix tries every card; it's merged and goes out with Thursday's deploy. Nothing to do on your side. Details: https://claude.ai/artifact/…

## Before publishing

Read only the TL;DR and each section's first line: do you know what happened and what to do next? `verify.sh` shows no ✗ and no readability ⚠; deprecations say gone vs kept; each diagram's type fits its question.
