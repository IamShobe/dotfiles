---
name: explainer-artifact
description: Build a human-facing "explainer" artifact that summarizes a change, feature, refactor, or migration — for teammates and reviewers, not machines. Heavy on visuals, TLDR-first, no reading fatigue. Covers what changed, what was deprecated, and which interfaces changed (user-facing AND developer-facing). Use when the user says "create a summary artifact", "explain what changed", "write up this feature/PR/refactor", "make a doc for the team", or asks to document a merged change visually.
allowed-tools: Read, Edit, Write, Bash, Grep, Glob, Skill, Artifact, AskUserQuestion
---

# Explainer Artifact

A one-page, **visual** explainer of a change — read by humans (teammates, reviewers, future you), never by a machine. The goal: someone grasps *what changed and why it matters* in under two minutes of scanning, without reading every word.

This skill owns the **content** — what to say, in what order, how to compress it. It **builds on the `web-artifacts-builder` skill**, which owns the mechanics (React + shadcn/ui + rich libs → one self-contained `bundle.html`). You write an `App.tsx`; `web-artifacts-builder` bundles it. Don't hand-write raw HTML or vendor CDN scripts — that's obsolete.

`web-artifacts-builder` ships in the same repo as this skill; `scripts/ensure-deps.sh` (step 0 below) locates it and installs its template deps on first use. Run it before building — never assume the toolchain is warm.

**Repo-agnostic.** Nothing here is tied to a particular codebase: the repo slug, commit SHA, and every example come from whatever checkout you're pointed at. The palette in `web-artifacts-builder`'s `template/src/theme.tsx` is a neutral default — swap those hexes to match your product.

## Non-negotiables (this is the whole point)

- **TLDR-first.** The hero states the thesis in one sentence. Every section leads with its takeaway, then supports it. A reader who stops after the first line of each section still gets it.
- **Visual over prose.** Prefer a diagram, a before/after pair, a diff-chip, a table, a numbered flow. If a paragraph can be a picture, make it a picture. Target: no block of prose longer than ~3 lines.
- **No reading fatigue.** Short sections, generous whitespace, scannable. If a section feels like a wall, split or cut it.
- **No bullshit / no AI filler.** Cut anything that doesn't inform a human: KPI vanity-metric strips ("5 files removed!"), restating the obvious, marketing tone, hedging. If a line wouldn't survive a teammate asking "so what?", delete it.
- **Concrete, real examples.** Use actual identifiers, real code/config from the change, real names — never lorem or invented placeholders. Pull them from the diff/source.

## Before writing — gather the facts

Don't guess. Extract the truth from the change:

```bash
git diff --name-only <base>...<branch>        # scope
git log --oneline <base>..<branch>            # the story
```

Then pin down, from the actual source:
- **The core shift** — the one conceptual change everything else follows from.
- **Deprecated / removed** — deleted files, retired APIs, dead flags. For each: *what* and *one-line why*. Distinguish **gone for good** from **kept as fallback** (say "don't build on these").
- **Interface changes** — split **user-facing** (what a person using the product sees) from **developer-facing** (types, signatures, schemas, endpoints). Show old → new.
- **Migration / compatibility** — DB migrations, snapshot/back-compat behavior, follow-up tickets.
- **Anything important** — a real bug the change fixes, "how to extend it now" (e.g. how to add a new X), a gotcha.

Verify examples against the code before putting them in — a wrong example is worse than none.

## Section menu (use what the change needs, in this order)

Not every change needs every section. Pick the ones that carry information; drop the rest.

1. **Hero** — eyebrow (ticket/status) · title · one-sentence thesis · a few context pills. No metric tiles.
2. **The core shift** — the central before→after idea. Often two cards or a single diagram. This is the "why".
3. **What changed for users** — before/after of the product surface. Only if user-facing.
4. **How it works** — one diagram of the new data/flow.
5. **Interface changes** — cards/table of old → new, with +/− diff-chips. Separate user-facing from developer-facing.
6. **Deprecated & removed** — "deleted" table vs "kept as fallback" chips.
7. **How to extend / use it now** — numbered steps with real copy-pasteable code, if the change adds an extension point.
8. **Migration notes** — DB, back-compat, follow-up tickets. Short.

Merge or rename freely. A tiny change might be just Hero + Interface changes + Migration.

## Visual vocabulary → how to build each in React

Reach for these; build them with shadcn + the template's rich libs (all pre-installed, imported directly, bundled inline).

| Device | Build with |
|---|---|
| Before/After cards | two shadcn `Card`s side by side, or old→new with a `lucide-react` `ArrowRight` |
| Diff-chips (`+ added` / `− removed`) | inline `<span>`s with green/red Tailwind classes |
| Emphasize a word in prose | `RoughNotation` (`react-rough-notation`) — highlight/circle/underline/strike. **Breaks inside the TOC's own-scroll-container** (below) — the mark detaches from its text on scroll. If this page has a side-rail TOC, use a plain CSS highlight `<span>` instead (see `libraries.md`). |
| Flow / sequence / state diagram | `import mermaid`, render in a `useEffect`; **color-code by role**, 4–7 nodes — see `web-artifacts-builder`'s `references/mermaid.md`. Native `<pre className="mermaid">` does **not** work bundled. |
| Hover to reveal detail | `Tippy` (`@tippyjs/react`) — wrap a `<span>` |
| Call out *the* line in code | `Highlight` (`prism-react-renderer`) |
| Charts | `recharts` (only if a number genuinely needs a chart — usually a table is better) |
| Visual/UI before/after wipe | `ReactCompareSlider` (`react-compare-slider`) — data-URI images |
| Arrows between elements | `LeaderLine` (`leader-line`) — init in `useEffect` |
| Tables (matchers, deprecations, status) | shadcn `Table` with a mono column for identifiers |
| Mini-mockups of a UI change | draw the real tile/badge with JSX + Tailwind, or inline `<svg>` |
| Callouts ("why this matters") | one per section max — a bordered `div` with an accent left-border |

**Icons:** `lucide-react` for UI glyphs (`import { Shield, Zap } from 'lucide-react'`). Brand logos (AWS, GitHub, Postgres…): inline a Simple-Icons `<svg fill="currentColor">`. Never a placeholder glyph like □.

**Size discipline:** unused imports tree-shake out, so import only what a section uses. `import mermaid` (the JS API) adds ~3MB — spend it only when the change genuinely needs a diagram.

## Table of contents (fixed side-rail)

3+ top-level sections → a fixed side-rail TOC, one link per top-level `<h2>`, top-level only. **Don't hand-roll it** — the iframe has no scroll viewport, which defeats `sticky`/`100vh`/hash-anchors/`window`-scroll/auto-root libs, and a hand-rolled observer flashes/mis-highlights. Use the vendored `Scrollspy` + own-scroll-container pattern: scaffold + jitter-free CSS in `web-artifacts-builder`'s `references/recipes.md`. If `scrollspy.tsx` isn't in the template, vendor it (same file) and `rm -rf <clone>` before rebuild (stale-clone gotcha).

## GitHub source links (commit-pinned permalinks)

Link each real code reference to its exact source lines. Derive the repo slug and SHA from the checkout itself — never hardcode:

```bash
git remote get-url origin   # → owner/repo (strip scheme, user, .git suffix)
git rev-parse HEAD          # → the pinned SHA
```

Build `github.com/<owner>/<repo>/blob/<sha>/<path>#L<start>-<end>`. **Verify each path + line range against the file** (a wrong line is worse than none); prefer a range over a bare line; link only genuine files. If the remote isn't GitHub (GitLab, Bitbucket) adjust the URL shape, and if there's no remote at all, skip the links rather than invent them. `gh()` helper: `references/recipes.md`.

## Design — product theme, professional

An explainer is an internal doc for teammates: match the product's theme, read as polished and utilitarian — real hierarchy, restraint. No neon/scanlines/gimmick palette.

**Use the shipped theme, don't re-emit tokens.** Render `<Theme/>` once near the root (`import { Theme } from '@/theme'`) — it wires the token palette as CSS vars, both light + dark. Style everything through the vars:
- `--bg --surface --border --border-hi` · text `--ink --ink-2 --ink-3`
- `--brand` = the **one** accent: eyebrow, active TOC, section rules, single call-to-attention. `--brand-ink` for on-hover/emphasis, `--brand-soft` for tint fills.
- `--signal` = highlight only (an attention badge, a RoughNotation) — spend sparingly, not a second accent.
- diff: `--add/--add-soft` (green) · `--rm/--rm-soft` (red). Code: `--code-bg/--code-ink`.

Type: sans body + `.mono` for code/identifiers/eyebrows (no display serif). ~65ch measure, `tabular-nums` in data columns. Raw hex ↔ token map, and how to re-skin: `references/theme-tokens.md`.

**Load `artifact-design`** for craft mechanics (type scale, `@font-face`) — but the shipped palette *is* the direction, so the vars above override "pick something distinctive". Wide content gets `overflow-x`.

## Build & publish

0. **Resolve the dependency** (idempotent; installs the template's deps on first use only) and capture the repo slug + SHA for permalinks:
   ```bash
   WAB="$(bash <this-skill>/scripts/ensure-deps.sh)"   # → path to web-artifacts-builder
   git remote get-url origin && git rev-parse HEAD
   ```
   List the top-level section ids for the TOC.
1. Draft the content per the section menu, then write it as a single **`App.tsx`** (React + shadcn + the libs above) to the scratchpad. Render `<Theme/>` once, style via the vars, include the fixed side-rail TOC and commit-pinned source links. **Start the file with a `// @title: <Human Readable Title>` line** — that becomes the browser-tab and Artifact-gallery name; without it the title falls back to `<name>`.
2. Build in one call:
   ```bash
   bash "$WAB/scripts/make-artifact.sh" <name> <your-App.tsx>   # → <name>/bundle.html
   ```
3. **Never publish `bundle.html` directly** — the artifact's tab/gallery identity is the published file's *basename*, so it would show up as "bundle". Copy it to a descriptive name first and publish that path (and keep re-publishing the same path on edits to preserve the URL):
   ```bash
   cp <name>/bundle.html <name>.html   # e.g. auth-rewrite-explainer.html
   ```
   Publish `<name>.html` via `Artifact` — emoji `favicon`, one-sentence `description`. Artifacts start private; the user shares if they want.

Then **stop and let the user prune.** Expect "delete that", "too AI", "fix that visual". Edit `App.tsx`, re-run `make-artifact.sh <name>` (warm rebuild ~0.35s), re-publish the same path.

## Compression checklist (before publishing)

- [ ] Hero thesis is one sentence a non-author understands.
- [ ] Every section's first line is its takeaway.
- [ ] No vanity-metric strip, no filler, no marketing voice.
- [ ] Deprecations answer "gone" vs "kept-but-don't-use".
- [ ] Interface changes split user-facing vs developer-facing, old→new.
- [ ] At least one real diagram / before-after / mockup.
- [ ] Every code/config example is real and verified against source.
- [ ] `// @title:` set in `App.tsx`; confirm with `grep -o '<title>[^<]*' <name>/bundle.html` — never ship a template default.
- [ ] `<Theme/>` rendered; styled via vars; both themes look right; any rich lib earns its place.
- [ ] 3+ sections → fixed side-rail TOC (vendored `Scrollspy`) with each top-level heading.
- [ ] If a TOC is present: `grep -n RoughNotation App.tsx` returns nothing (it detaches from text on scroll inside the TOC's own-scroll-container — swap for a plain CSS highlight `<span>`).
- [ ] Code refs link to commit-pinned GitHub permalinks; every path + line range verified against source.
