---
name: explainer-artifact
description: Build a human-facing "explainer" artifact that summarizes a change, feature, refactor, or migration — for teammates and reviewers, not machines. Heavy on visuals, TLDR-first, no reading fatigue. Covers what changed, what was deprecated, and which interfaces changed (user-facing AND developer-facing). Use when the user says "create a summary artifact", "explain what changed", "write up this feature/PR/refactor", "make a doc for the team", or asks to document a merged change visually.
allowed-tools: Read, Edit, Write, Bash, Grep, Glob, Skill, Artifact, AskUserQuestion
compatibility: Needs Node 18+, pnpm or npm, python3, and git. Uses the web-artifacts-builder and diagram-design skills; scripts/ensure-deps.sh fetches any that are missing.
metadata:
  requires: "web-artifacts-builder diagram-design"
  requires-sources: "IamShobe/dotfiles cathrynlavery/diagram-design"
---

# Explainer Artifact

A one-page, **visual** explainer of a change — read by humans (teammates, reviewers, future you), never by a machine. The goal: someone grasps *what changed and why it matters* in under two minutes of scanning, without reading every word.

This skill owns the **content** — what to say, in what order, how to compress it. It **builds on the `web-artifacts-builder` skill**, which owns the mechanics (React + shadcn/ui + rich libs → one self-contained `bundle.html`). You write an `App.tsx`; `web-artifacts-builder` bundles it. Don't hand-write raw HTML or vendor CDN scripts — that's obsolete.

**Dependencies.** This skill needs two other skills, `web-artifacts-builder` (build toolchain) and `diagram-design` (diagrams), plus the `explainer` diagram profile. `scripts/ensure-deps.sh` (step 0 below) resolves all three: it uses installed copies when present, fetches any missing skill into `.deps/`, installs the template's node deps, and installs the profile. It's idempotent. Run it before building; never assume the toolchain is warm.

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
| Any diagram — flow, sequence, state, architecture, layer stack, timeline… | the **`diagram-design`** skill → inline its `<svg>` as a component. See §Diagrams below. **Never `import mermaid`.** |
| Hover to reveal detail | `Tippy` (`@tippyjs/react`) — wrap a `<span>` |
| Call out *the* line in code | `Highlight` (`prism-react-renderer`) |
| Charts | `recharts` (only if a number genuinely needs a chart — usually a table is better) |
| Visual/UI before/after wipe | `ReactCompareSlider` (`react-compare-slider`) — data-URI images |
| Arrows between elements | `LeaderLine` (`leader-line`) — init in `useEffect` |
| Tables (matchers, deprecations, status) | shadcn `Table` with a mono column for identifiers |
| Mini-mockups of a UI change | draw the real tile/badge with JSX + Tailwind, or inline `<svg>` |
| Callouts ("why this matters") | one per section max — a bordered `div` with an accent left-border |

**Icons:** `lucide-react` for UI glyphs (`import { Shield, Zap } from 'lucide-react'`). Brand logos (AWS, GitHub, Postgres…): inline a Simple-Icons `<svg fill="currentColor">`. Never a placeholder glyph like □.

**Size discipline:** unused imports tree-shake out, so import only what a section uses. Diagrams cost nothing at bundle time — they're static inline `<svg>`, no renderer shipped.

### Diagrams — always `diagram-design`, one pass

**Every diagram comes from the `diagram-design` skill.** No mermaid, no hand-rolled boxes-and-arrows SVG: mermaid's auto-layout is the "AI slop" look an explainer avoids, and it ships a ~3MB renderer to draw six boxes. At most **3 diagrams per page**; if a point doesn't need one, cut it.

**Fast path. The explainer has already decided palette, plan, and output shape, so these diagram-design steps are skipped:**

| diagram-design says | In an explainer |
|---|---|
| §0 style-guide gate, onboarding, `/diagram-design:profile` | **Skip.** Read `~/.diagram-design/profiles/explainer.md` once as the style guide. Never ask about branding, never save or load a profile. |
| §3 "confirm before drawing" pause | **Skip.** Your one diagram plan (below) is the confirmation. |
| Page chrome: eyebrow, `<h1>`, Instrument Serif, dark/full variants, motion, export | **Skip.** Only the `<svg>` survives conversion. Start from `assets/template.html`, draw light only. |
| §9 typography checks (`getComputedStyle`, font verification) | **Skip.** The page's `<Theme/>` sets fonts. |
| §6 connector rules, §7 complexity budget, `<title>`/`<desc>` | **Keep.** These are what make the diagram good. |
| `self_check.py` | **Automatic.** The converter runs it. |

Procedure:

1. **Plan all diagrams in one line each**: `<slug> · <type> · <what it shows>`. Load diagram-design's SKILL.md **once per page** (or `$DIAGRAM_DESIGN/SKILL.md` if it isn't registered with your agent), then only the `references/type-<type>.md` each diagram needs.
2. **Write each diagram** to `<slug>.html` (kebab-case slug) in the scratchpad, using the explainer profile's hexes.
3. **Convert all of them in one call.** This also creates the build workspace:
   ```bash
   bash <this-skill>/scripts/diagram-to-jsx.sh <name> a.html b.html c.html   # → <name>/src/diagrams/<slug>.tsx
   ```
   It self-checks each file, maps every palette color (explainer or diagram-design default, hex or rgba) to theme vars, prefixes ids per diagram, escapes JSX text, and prints the import lines to paste.

**No restyle loop.** Colors and dark mode belong to the converter: never hand-edit hexes or vars in `src/diagrams/*.tsx`. An "off-palette, kept as drawn" note is informational, so leave it. If the converter fails, fix that one `.html` and re-run it for that file only. If a diagram still looks wrong after **one** redraw, cut it rather than iterate.

**Fonts.** Diagrams use Geist + Geist Mono. Add one `<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&display=swap">` to `index.html` (CSP-allowed). Without it they fall back to system sans, which is fine.

## Table of contents (fixed side-rail)

3+ top-level sections → a fixed side-rail TOC at `lg:` and up, one link per top-level `<h2>`, top-level only. **The rail is desktop-only** — hide it below `lg` (`hidden lg:block`) and drop the content gutter with it; a 240px rail on a 500px-wide iframe leaves an unreadable column. **Don't hand-roll it** — the iframe has no scroll viewport, which defeats `sticky`/`100vh`/hash-anchors/`window`-scroll/auto-root libs, and a hand-rolled observer flashes/mis-highlights. Use the vendored `Scrollspy` + own-scroll-container pattern: scaffold + jitter-free CSS in `web-artifacts-builder`'s `references/recipes.md`. If `scrollspy.tsx` isn't in the template, vendor it (same file) and `rm -rf <clone>` before rebuild (stale-clone gotcha).

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

**Dark mode is not an afterthought — build in it, not just check it.** The page is read in both, and dark is where explainers usually fall apart. Rules:

- **Never a raw hex, never a Tailwind color class** for anything themed. `bg-white`, `text-gray-600`, `border-gray-200`, `bg-slate-50` are all light-mode-only and are the #1 cause of a broken dark page. Style through the vars: `style={{background:'var(--surface)', color:'var(--ink-2)'}}`. Tailwind is for layout and spacing, not color.
- **Elevation comes from `--surface`, not from shadow or a lighter gray.** Shadows are invisible on a dark ground. A card is `--surface` on `--bg` with a `--border` hairline.
- **Don't hand-tune per-theme.** If a thing needs different colors in each theme, you picked the wrong var — there's no `dark:` variant in this system.
- **Opacity over invented tints.** For a wash, use `color-mix(in srgb, var(--brand) 12%, transparent)` — it tracks both themes. A hardcoded `#eef2ff` glows in dark mode.
- **Anything with its own background** — code blocks, inline `<svg>`, data-URI images, `ReactCompareSlider` screenshots — does **not** inherit the theme. Code blocks are fine (`--code-bg` is dark in both by design). Screenshots of a light UI will sit as a white slab on a dark page: that's acceptable if it's deliberately a screenshot, but give it a `--border` frame so it reads as an image rather than a rendering bug.

**Load `artifact-design`** for craft mechanics (type scale, `@font-face`) — but the shipped palette *is* the direction, so the vars above override "pick something distinctive". Wide content gets `overflow-x`.

**Use the full viewport.** Never default to a narrow reading column: `main` at `max-w-[1280px]` (`2xl:max-w-[1480px]`) beside the rail gutter, with tables, grids, diagrams, and mockups spanning the full content width. Constrain *prose* legibility per-paragraph (`maxWidth: '88ch'` on the paragraph component), not by shrinking the page — a `max-w-3xl` page wastes most of the screen and squeezes every table.

**Full viewport means the viewport it actually gets.** The same page is read in a full browser tab, in a side-by-side split, and in a phone-width artifact iframe. "Full width" is a *maximum*, never a floor — see the next section.

## Narrow widths (the squash rule)

The artifact iframe is frequently far narrower than a laptop tab. The failure mode is always the same: a layout that keeps its desktop shape and *compresses* — three columns crushed to 90px each, a table with one word per line, a diagram shrunk to illegible. **Content must reflow, never squash.** One breakpoint does most of the work — `md` (768px) — with `lg` (1024px) for the rail.

Rules, in the order they break:

- **Every multi-column grid starts at one column.** Write `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`, never a bare `grid-cols-3`. Same for flex rows of cards: `flex-col md:flex-row`.
- **Never fix a width in `px` or `vw` on content.** No `w-[720px]`, no `min-w-[600px]` on a section. Use `max-w-*` (a cap) plus `w-full` (a fill). A `min-width` on anything but a table cell is the bug.
- **Wide-by-nature content scrolls in its own box, and only that box.** Tables, code blocks, diagrams, and mockups go in `<div className="w-full overflow-x-auto">`. The page body must never scroll sideways.
- **Tables:** give the wrapper `overflow-x-auto` and the `<table>` `min-w-[560px]` so columns keep their shape and the wrapper scrolls, instead of every cell wrapping to four lines. For a 2-column key/value table, prefer stacking to definition-list rows below `md` over horizontal scroll.
- **Diagrams keep `viewBox` + `w-full h-auto`** (already the rule above) — that scales them, but an architecture SVG below ~600px is unreadable at any scale. Wrap it in `overflow-x-auto` and give the `<svg>` `min-w-[640px]` so it scrolls rather than shrinks to nothing.
- **Padding and type step down:** `p-4 md:p-8`, `text-3xl md:text-5xl` on the hero. Desktop-tuned padding eats a third of a narrow screen.
- **Side-by-side comparisons** (before/after, `ReactCompareSlider`, two code panes) stack vertically below `md`. A 2-up diff at 380px each is worse than nothing.
- **Sticky/fixed anything is desktop-only.** The rail, any sticky header — `hidden lg:block`. Vertical space is the scarce resource on a narrow screen.

**Check it before publishing.** Open `bundle.html` in the browser and resize to ~390px and ~768px, or use `claude-in-chrome` / `playwright-cli` to screenshot at those widths. Look for: horizontal page scroll, a crushed grid, a table with one word per line, text under ~14px. Any of those → fix it, don't ship it.

## Build & publish

0. **Resolve the dependency** (idempotent; installs the template's deps on first use only) and capture the repo slug + SHA for permalinks:
   ```bash
   eval "$(bash <this-skill>/scripts/ensure-deps.sh)"   # sets $WAB and $DIAGRAM_DESIGN (skill dirs)
   git remote get-url origin && git rev-parse HEAD
   ```
   List the top-level section ids for the TOC.
1. **Diagrams first**, per §Diagrams: plan, draw, then one `diagram-to-jsx.sh <name> *.html` call. Do this before writing `App.tsx`, because a page drafted first grows SVG placeholders that never get replaced.
2. Draft the content per the section menu, then write it as a single **`App.tsx`** (React + shadcn + the libs above) to the scratchpad. Render `<Theme/>` once, style via the vars, include the fixed side-rail TOC and commit-pinned source links. **Start the file with a `// @title: <Human Readable Title>` line** — that becomes the browser-tab and Artifact-gallery name; without it the title falls back to `<name>`.
3. Build in one call:
   ```bash
   bash "$WAB/scripts/make-artifact.sh" <name> <your-App.tsx>   # → <name>/bundle.html
   ```
4. **Never publish `bundle.html` directly** — the artifact's tab/gallery identity is the published file's *basename*, so it would show up as "bundle". Copy it to a descriptive name first and publish that path (and keep re-publishing the same path on edits to preserve the URL):
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
- [ ] Every diagram went through `diagram-to-jsx.sh` (it enforces self-check, `viewBox`, `<title>`/`<desc>`, theme vars), and `grep -n mermaid App.tsx` returns nothing.
- [ ] Every code/config example is real and verified against source.
- [ ] `// @title:` set in `App.tsx`; confirm with `grep -o '<title>[^<]*' <name>/bundle.html` — never ship a template default.
- [ ] `<Theme/>` rendered; styled via vars; any rich lib earns its place.
- [ ] **Dark mode actually checked**, not assumed — toggle it and read the whole page.
- [ ] No hardcoded colors: `grep -nE '(bg|text|border|from|to)-(white|black|gray|slate|zinc|neutral|stone|indigo|blue|red|green|amber)-?[0-9]*|#[0-9a-fA-F]{6}' App.tsx src/**/*.tsx` returns nothing outside `src/theme.tsx` and `src/diagrams/` (the converter owns those).
- [ ] No `shadow-*` class — elevation is `--surface` + `--border`.
- [ ] 3+ sections → fixed side-rail TOC (vendored `Scrollspy`) with each top-level heading.
- [ ] **Checked at ~390px and ~768px**, not just laptop width: no horizontal page scroll, no crushed grid, no one-word-per-line table, nothing under 14px.
- [ ] No bare multi-column grid: `grep -nE 'grid-cols-[2-9]' App.tsx src/**/*.tsx` — every hit is prefixed `md:` or `lg:`, with a `grid-cols-1` base.
- [ ] No fixed content widths: `grep -nE '\b(w|min-w)-\[[0-9]+(px|vw)\]' App.tsx src/**/*.tsx` returns nothing outside `overflow-x-auto` wrappers (tables/diagrams may set `min-w`).
- [ ] Side-rail and any sticky element are `hidden lg:block`; the content gutter drops with them.
- [ ] If a TOC is present: `grep -n RoughNotation App.tsx` returns nothing (it detaches from text on scroll inside the TOC's own-scroll-container — swap for a plain CSS highlight `<span>`).
- [ ] No `flex`/`inline-flex` component (an icon+link like `SourceLink`, an inline badge) sits inside a sentence of running prose — it breaks text reflow and can glue words together at a line wrap (see `libraries.md`). Fine for block-level layout (cards, badge rows), not for something a sentence flows around.
- [ ] Code refs link to commit-pinned GitHub permalinks; every path + line range verified against source.
