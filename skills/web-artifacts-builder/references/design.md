# Design rules for custom JSX

The kit already follows all of this. Read it before writing a component the kit doesn't
have (a UI mockup, a custom chart) or styling values inside kit blocks. `verify.sh` checks
the rules marked ✔.

## Theme

Style every color through the vars `<Page>` provides:

- Surfaces: `--bg --surface --border --border-hi`. Text: `--ink --ink-2 --ink-3`.
- `--brand` is the **one** accent (eyebrow, active TOC, the single call to attention). Use `--brand-ink` for emphasis and `--brand-soft` for tint fills.
- `--signal` is for highlights only, sparingly. Diffs: `--add/--add-soft`, `--rm/--rm-soft`. Code: `--code-bg/--code-ink`.
- ✔ **No raw hex, no Tailwind color classes** (`bg-white`, `text-gray-600` are light-only and break dark mode). Write `style={{ color: 'var(--ink-2)' }}`; Tailwind is for layout.
- ✔ **No shadows.** Elevation is `--surface` on `--bg` plus a `--border` hairline.
- Tints: `color-mix(in srgb, var(--brand) 12%, transparent)`, never an invented hex. No `dark:` variants: if something needs different colors per theme, you picked the wrong var.
- Screenshots of a light UI stay light on a dark page. That's fine if they're framed with `--border` so they read as images.
- Sans body, `.mono` for identifiers, no display serif, `tabular-nums` in data columns. To re-skin, edit `web-artifacts-builder/template/src/theme.tsx`; hex values are in `theme-tokens.md`.

## Color carries meaning

Each color says one thing, everywhere on the page, so the eye learns it once:

- `--rm` red: removed, broken, damage done, the bad outcome. `--add` green: added, fixed, the good outcome. `--brand`: the new state and the one thing to look at. `--ink-3` / dimmed: context, unchanged.
- Color marks a **value** (a chip, an icon, a cell tint), never a paragraph. Body text stays `--ink` / `--ink-2`; a red sentence is hard to read and says nothing a red chip doesn't.
- A status is shape + color (✓ in a green circle, `−` chip), never color alone.

## Type carries meaning

- `.mono` only for real identifiers: code names, ids, file names, env vars. A plain-words label in mono reads as code.
- Small caps (`.mono text-xs uppercase`) for structural labels: column titles, "Example", "In short", areas. One weight of emphasis per block.

## Interaction is whole

- A hover or active state covers the whole row or card, edge to edge, as one even tint. Tinting each child separately leaves patches wherever there is padding or a gap between children.
- Cells that fill their row (no gap, no padding between them) may tint per cell, to keep their own fills.
- Anything clickable looks clickable at rest (a bordered pill, an underline), not only on hover.
- Controls stay in view with what they control: an interactive widget's pickers and toggles go in `<Playground controls>`, and a chart's zoom bar is always shown, never only on hover or when shrunk.
- Every chart or diagram the reader may need to inspect can zoom and pan (`<Figure>`). Size a diagram to fit; the reader zooms in, the page never makes them scroll through it.

## Every block earns its space

This is a working document, not a landing page. A block that repeats what is already on screen (a second table of contents, a summary of the summary, a card per heading) or holds a few words in a large box is cut. Navigation aids stay compact: one rail on wide screens, one collapsed line on narrow ones.

## Narrow widths: reflow, never squash

The artifact iframe is often phone-width.

- ✔ Grids start at one column: `grid-cols-1 md:grid-cols-2`. Same for flex rows: `flex-col md:flex-row`.
- ✔ No fixed `px`/`vw` widths on content. Use `max-w-*` plus `w-full`.
- ✔ Wide content (tables, code, diagrams, mockups) goes in `<div className="w-full min-w-0 overflow-x-auto">`. The page itself never scrolls sideways.
- Padding and type step down: `p-4 md:p-8`, `text-3xl md:text-5xl`.
- Side-by-side comparisons stack below `md`. Decorative sticky or fixed elements are `hidden lg:block`; controls stay (`<Playground>` pins them on top).
- A flex component never goes inside running prose; it breaks line wrapping. Inline elements only.
- RoughNotation detaches inside the page's scroll container, so use `<Mark>`.
