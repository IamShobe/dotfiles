---
name: explainer-artifact
description: Write a human-facing "explainer" artifact that summarizes a change, feature, refactor, or migration — for teammates and reviewers, not machines. Heavy on visuals, TLDR-first, no reading fatigue. Covers what changed, what was deprecated, and which interfaces changed (user-facing AND developer-facing). Use when the user says "create a summary artifact", "explain what changed", "write up this feature/PR/refactor", "make a doc for the team", or asks to document a merged change visually.
allowed-tools: Read, Edit, Write, Bash, Grep, Glob, Skill, Agent, Artifact, AskUserQuestion
compatibility: Needs Node 18+, pnpm or npm, python3, and git. Builds on the web-artifacts-builder skill (which uses diagram-design), installed by skillshare or the iamshobe marketplace; scripts/start.sh finds it.
metadata:
  requires: "web-artifacts-builder diagram-design"
  requires-sources: "IamShobe/dotfiles cathrynlavery/diagram-design"
---

# Explainer Artifact

A one-page, visual explainer of a change for people who didn't write it. A reader gets *what changed, why it matters and what to do* in under two minutes of scanning.

This skill owns the **story** (structure, formatting, content). `web-artifacts-builder` (`$WAB`) owns the mechanics (kit, theme, diagrams, build, verify). `S` = this skill's directory.

## Fewest turns

The cost is agent round-trips, not builds. A first publish takes **5 turns**; each later edit takes **1**.

| Turn | What you send (one response) |
|---|---|
| 1 | `bash $S/scripts/start.sh [base] [head] [-- paths…]`: paths, every rule file and the facts of the change, in one output |
| 2 | Every source read you need, in parallel (the *why*, exact line ranges); start the ✎ diagram subagent here if any |
| 3 | `Write specs.json` + `Write App.tsx` + `Bash build.sh …` together: plan in your head, not in a turn |
| 4 | All fixes for the ✗/⚠ lines and the contact sheet as `Edit`s + rebuild, in one pass |
| 5 | `Artifact` publish `<name>.html` (in turn 4 when turn 3's verify was clean) |
| edit | `Edit` App.tsx + `Bash build.sh <name>` + `Artifact` publish, in one response |

- Don't `Read` the rule files: `start.sh` printed them. Don't re-read a file you just wrote.
- `start.sh` prints absolute paths. Every shell is fresh, so use them; never rely on an earlier `eval`.
- ⚙ diagrams render inside the build, never as a separate step.
- Ask the user nothing before the first publish. They prune afterwards.

## Non-negotiables

1. **Readability is the core standard** (`references/readability.md`): outcome first, takeaways ≤ 25 words, paragraphs ≤ 60, numbers not adjectives, lists ≤ 5, one word per concept, no filler, end on one action.
2. **TL;DR first**: a `<Tldr>` (what broke, why, fix, status, what you do) and the main `<BeforeAfter>`, in plain words. Then the long version.
3. **Glance test** (`references/formatting.md`): each block makes its point to a reader who reads none of its sentences. One example, values not sentences, outcome first, why last.
4. **Introduce before you use**: every new word gets `<Term def>` at its first appearance, before any heading, diagram or table uses it.
5. **Real examples only**: identifiers, code and names from the change, verified against source. Every ticket and PR is a `<Ref>` link, every code mention a `<Src>`.

## Story

- **One arc**: context → what was wrong → the core shift → how it works now → what changes for the reader → what to do next. Cut a section that doesn't move it.
- **3–4 parts** with `group` (*What went wrong* → *The fix* → *Shipping* → *What's next*), section titles ≤ 4 words.
- **One running example** (a person, a request, a row) through the whole page, diagrams included.
- **A smart outsider**: knows the product, not this code.
- **Takeaway test**: the thesis plus each `takeaway`, read in order, is one coherent paragraph (`verify.sh` prints it). If not, reorder or cut.

From the facts, pin down: the core shift; what's gone for good vs kept as fallback; interface changes, user-facing vs developer-facing, old → new; migrations and follow-ups; status (merged ≠ deployed).

| Section | Kit |
|---|---|
| Hero: eyebrow with `<Ref>` links and status, title, thesis | `<Page eyebrow title thesis pills>` |
| TL;DR | `<Tldr>` + `<BeforeAfter example rows result>` |
| What changed for users (if any) | `<BeforeAfter>`, a mockup |
| How it works | one diagram in `<Figure>` |
| Interface changes | `<Changes>`, user-facing and developer-facing apart |
| Deprecated & removed | `<Deprecations>` |
| A number that moved | `<TimeChart>` with milestones |
| Rollout, how to extend | `<Steps>` |

## Diagrams (≤ 3)

Pick each type from `diagram-types.md` (printed by `start.sh`) by the question its section answers: a request path is a `sequence`, a status change a `state`, a migration a `db-schema`, a rollout a `gantt`. Never mermaid or hand-rolled boxes.

- **⚙ rendered types**: one `specs.json` array, passed to `build.sh --specs`. A rejected spec says what to fix; change the spec, never the output.
- **✎ hand-drawn types**: one background subagent, started in turn 2. Import names are predictable (`auth-flow` → `import { AuthFlow } from '@/diagrams/auth-flow'`), so write `App.tsx` meanwhile. Prompt:

> Draw these diagrams for an explainer page. No questions, no extra files. Read `$WAB/references/diagram-brief.md`, then for each diagram only `$DIAGRAM_DESIGN/references/type-<type>.md`. Plans: `<slug · type · question>`. Vocabulary: `<terms>`. Write each to `<dir>/<slug>.html` containing only the `<svg>`. From `<dir>`, run `bash $WAB/scripts/diagram-to-jsx.sh <name> <files>`; fix a rejected file once. Never edit the generated .tsx. Reply with only the import lines.

## App.tsx and build

First line `// @title: <Human Title>`; content only, with the kit.

```tsx
// @title: Checkout Tries Every Card
import { Page, Section, Tldr, BeforeAfter, Ref } from '@/kit'
export default function App() {
  return <Page meta={meta} eyebrow={<>…</>} title="…" thesis="…">
    <Section id="tldr" title="TL;DR"><Tldr items={[…]} /><BeforeAfter … /></Section>
  </Page>
}
```

`build.sh` renders the specs, bundles and runs `verify.sh`: story (takeaway paragraph, term order, jargon), `<Src>` links at a pushed SHA, theme and style, overflow and tiny text at 3 widths, readability ⚠, and one light+dark contact sheet. Read the sheet once; fix everything in one pass.

Publish `<name>.html` (never `bundle.html`) with a one-sentence `description`; re-publish the same path to keep the URL. Then stop and let the user prune.

## Before publishing

Read only the TL;DR and each section's first line: do you know what happened and what to do next? `verify.sh` shows no ✗ and no readability ⚠; deprecations say gone vs kept; each diagram's type fits its question.
