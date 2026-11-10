---
name: explainer-artifact
description: Write a human-facing "explainer" artifact that summarizes a change, feature, refactor, or migration — for teammates and reviewers, not machines. Heavy on visuals, TLDR-first, no reading fatigue. Covers what changed, what was deprecated, and which interfaces changed (user-facing AND developer-facing). Use when the user says "create a summary artifact", "explain what changed", "write up this feature/PR/refactor", "make a doc for the team", or asks to document a merged change visually.
allowed-tools: Read, Edit, Write, Bash, Grep, Glob, Skill, Agent, Artifact, AskUserQuestion
compatibility: Needs Node 18+, pnpm or npm, python3, and git. Builds on the web-artifacts-builder skill (which uses diagram-design), installed by skillshare or the iamshobe marketplace; scripts/ensure-deps.sh finds it.
metadata:
  requires: "web-artifacts-builder diagram-design"
  requires-sources: "IamShobe/dotfiles cathrynlavery/diagram-design"
---

# Explainer Artifact

A one-page, **visual** explainer of a change, read by humans (teammates, reviewers, future you). The goal: someone grasps *what changed and why it matters* in under two minutes of scanning.

This skill owns the **story**: structure, formatting and content. Everything mechanical (page kit, theme, diagram renderer, build, QA) is `web-artifacts-builder`'s, and every step below is one call.

`S` = this skill's directory. Run `eval "$(bash $S/scripts/ensure-deps.sh)"` once per shell: it sets `$WAB` (web-artifacts-builder's directory) and `$DIAGRAM_DESIGN`. Nothing here is tied to one repo.

## Non-negotiables

- **TL;DR first, and visual.** The hero states the thesis in one sentence; the first section is a TL;DR: a `<Tldr>` (what broke, why, the fix, status, what you do; ≤ 8-word statements, numbers as pills) and the main before → after, in plain words. Only then the long version. Every section opens with its takeaway.
- **Visual over prose: the glance test.** Every block makes its point to a reader who reads no sentence in it: one concrete example, values not sentences, outcome first, explanation last. The principles and which block fits which content: `references/formatting.md`. No prose block over ~3 lines.
- **No filler.** No vanity-metric strips ("5 files removed!"), no restating the obvious, no marketing voice, no hedging. If a line wouldn't survive "so what?", delete it.
- **Real examples only.** Actual identifiers, code and names from the change, verified against source. A wrong example is worse than none.

## Story: one coherent narrative

The page is read top to bottom by someone who didn't write the change. Write it as a story, not a list of facts.

- **One arc.** Context → what was wrong or missing → the core shift → how it works now → what changes for the reader → what to do next. Each section answers the question the previous one raised. Cut any section that doesn't move the arc.
- **Introduce before you use.** Every new word (a new concept, an internal name, an acronym, a renamed thing) is defined in plain words at its **first** appearance, with `<Term def="…">`, before any heading, TL;DR card, rail entry, diagram or table relies on it. Where the idea is needed earlier, say it in plain words. No forward references ("see below for what X is").
- **Tell it in parts.** Group the sections after the TL;DR into 3–4 story parts with `group` (*What went wrong* → *The fix* → *Shipping* → *What's next*), section titles ≤ 4 words saying what the reader learns. The rail then reads as the story.
- **One name per thing.** Pick one word for each concept and keep it everywhere: prose, diagram labels, tables, code comments. Don't let "workspace", "project" and "space" all mean the same thing.
- **Assume a smart outsider.** A teammate from another area: knows the product, not this code. Explain domain terms they'd lack, and skip what they already know.
- **Carry one running example** through the page (the same request, record or user) instead of a new example per section.
- **The takeaway test.** Read only the thesis plus each section's `takeaway`, in order. It must read as one coherent paragraph. If it doesn't, the structure is wrong: fix the order or cut, don't polish sentences.

## Workflow

### 1. Facts: one call

```bash
bash $S/scripts/gather-facts.sh [base] [head] [-- paths…]   # base: merge-base with the default branch
```

Pass `-- <paths>` whenever the change lives in part of a big repo (one package, one service); the commit list and diff then contain only what matters.

It returns the `meta` line for `<Page>`, the commits, files by status, changed declarations as `path:start-end` (paste straight into `<Src lines>`), link ranges per file, migrations and dependency changes. Then read only the source you need for the *why* and for the exact line ranges you'll link. From that, pin down:

- **The core shift**: the one conceptual change everything else follows from.
- **Deprecated / removed**: *what* plus a one-line *why*. Separate **gone for good** from **kept as fallback** ("don't build on these").
- **Interface changes**: **user-facing** (what a person using the product sees) vs **developer-facing** (types, signatures, schemas, endpoints), old → new.
- **Migration / compatibility**: DB migrations, back-compat, follow-up tickets.
- **Anything important**: a real bug it fixes, how to extend it now, a gotcha.

### 2. Story plan: before any code

Write the thesis and one takeaway per section, and run the takeaway test on them. Choose sections from this menu, in this order, and drop any that carry nothing; within a section, the block is chosen by what the content is (`references/formatting.md`):

| Section | Kit |
|---|---|
| Hero: eyebrow (ticket and PRs as `<Ref>` links, status), title, thesis, context pills | `<Page eyebrow title thesis pills>` |
| TL;DR: what broke, why, the fix, status, what you do — then the picture | `<Tldr>` + the core shift as `<BeforeAfter example rows result>` |
| What changed for users (only if user-facing) | `<BeforeAfter example …>`, mockup |
| How it works: the new flow | one diagram in `<Figure>` |
| Interface changes | `<Changes>` (user-facing and developer-facing kept separate) |
| Deprecated & removed | `<Deprecations>` |
| How to extend / use it now | `<Steps>` with real code |
| Migration notes | short `<P>` or `<Table>` |

Then plan the diagrams, **at most 3**, one line each: `<slug> · <type> · <the question it answers>`. **Choose each type from `$WAB/references/diagram-types.md` by the question its section answers**, not by habit: a request path is a `sequence`, a status change is a `state`, a migration is a `db-schema`, a perf win is a `dumbbell` or `waterfall`, a rollout is a `gantt`. Two diagrams of the same type on one page need a reason. Labels use the page's vocabulary; a diagram never introduces a term the prose hasn't introduced first.

### 3. Diagrams: specs, one call

Every diagram follows diagram-design's rules. Never use mermaid or hand-rolled boxes and arrows.

**⚙ rendered types (24, most of what an explainer needs):** write one `specs.json` (an array, one spec per diagram). Start from `python3 $WAB/scripts/diagrams/render.py --example <type>`. Then:

Rendering happens inside the build (step 4). To check specs on their own first:

```bash
python3 $WAB/scripts/diagrams/render.py specs.json --artifact <name>   # renders, self-checks, converts → import lines
```

A diagram wider than ~1240px gets a warning with its effective text size: cut steps, lower `gap`, or split it. A spec that breaks a rule (over budget, a decision without labelled exits, a waterfall that doesn't add up) is rejected with the fix. Change the spec, never the output. Specs are small, so write them inline; no subagent is needed.

**✎ hand-drawn types** (fishbone, sankey, journey, loop and the rest in `$WAB/references/diagram-types.md`): delegate to one background subagent (Claude Code: `Agent`) while you write `App.tsx`, since import names are predictable (`auth-flow` → `import { AuthFlow } from '@/diagrams/auth-flow'`). Prompt:

> Draw these diagrams for an explainer page. No questions, no extra files. Read `$WAB/references/diagram-brief.md`, then for each diagram only `$DIAGRAM_DESIGN/references/type-<type>.md`. Plans: `<lines>`. Vocabulary: `<terms>`. Write each to `<dir>/<slug>.html` containing only the `<svg>`. Then, from `<dir>`, run `bash $WAB/scripts/diagram-to-jsx.sh <name> <files>`; fix a rejected file once. Never edit the generated .tsx. Reply with only the import lines.

`diagram-to-jsx.sh` maps every color to theme vars, including dark mode, prefixes ids, and sizes each diagram at its natural width. **Never hand-edit colors in a diagram.** If one still looks wrong after one fix, cut it.

### 4. Write `App.tsx` and build

Content only, with the page kit (`$WAB/references/kit.md`), formatted per `$S/references/formatting.md` (before → after, interface changes, tables). First line: `// @title: <Human Title>`.

```tsx
// @title: Projects Without Owners
import { Page, Section, BeforeAfter, Changes, P, Term, Src } from '@/kit'
import { HowItWorks } from '@/diagrams/how-it-works'
export default function App() {
  return <Page meta={meta} eyebrow="PR #412 · merged" title="…" thesis="…">
    <Section id="shift" title="The core shift" takeaway="…"><BeforeAfter example="…" rows={[…]} result={…} caption="…" /></Section>
  </Page>
}
```

**One call renders the specs, builds, and verifies** (step 5 runs automatically):

```bash
bash $WAB/scripts/build.sh <name> App.tsx --specs specs.json --repo <checkout>   # → <name>.html + the verify report
bash $WAB/scripts/build.sh <name>                                               # rebuild after an edit (also re-verifies)
```

Need a component the kit doesn't have? Follow `$WAB/references/design.md`.

### 5. Verify, then publish

`build.sh` ends by running `$WAB/scripts/verify.sh <name> [repo]` (run it alone with that command). It checks everything mechanical:
- **Story:** prints the takeaway paragraph, fails on any term used before its `<Term>` (diagrams included), and warns about jargon that was never introduced.
- **Source links:** every `<Src>` resolves at the pinned SHA (the file exists, the range fits), and the SHA is pushed.
- **Style:** theme vars only, no shadows, responsive grids, no fixed widths, a real title.
- **Layout:** an overflow and tiny-text probe at 390/768/1280px, and **one contact sheet** (light and dark × three widths).

Read the sheet once, fix every ✗ in a single edit pass, rebuild, re-run. Don't screenshot by hand.

Publish `<name>.html` with the `Artifact` tool (never `bundle.html`, whose basename becomes the title), with a one-sentence `description`. Re-publish the same path on edits to keep the URL.

Then **stop and let the user prune** ("delete that", "too AI"). Edit, `$WAB/scripts/build.sh <name>`, re-publish.

## Final check (content only; `verify.sh` covers the rest)

- [ ] The takeaway paragraph `verify.sh` prints reads as one coherent story.
- [ ] The TL;DR reads in seconds: ≤ 8-word statements leading with the outcome, numbers in `facts` pills, status honest (merged ≠ deployed) with links, a next-action row; then the main example. The rail shows 3–4 named parts with short titles.
- [ ] Every ticket, PR and doc is a `<Ref>` link, every code mention a `<Src>`; the status in the eyebrow is current.
- [ ] Each diagram's type fits the question its section answers (`$WAB/references/diagram-types.md`), not a default.
- [ ] Every block passes the glance test (`references/formatting.md`): one example, values not sentences, outcome first, the difference marked, the explanation last. No table of sentences.
- [ ] Thesis is one sentence a non-author understands. No filler, no vanity metrics.
- [ ] Deprecations say "gone" vs "kept, don't build on it". Interface changes split user-facing from developer-facing, old → new.
- [ ] Every example is real, from the diff. `<Src lines>` values come from `gather-facts.sh`'s link ranges.
- [ ] `verify.sh` shows no ✗, and the contact sheet looks right in both themes.
