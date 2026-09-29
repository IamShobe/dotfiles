# Design rules for custom JSX

The kit already follows all of this. Read it only when writing a component the kit
doesn't have (a UI mockup, a custom chart). `verify.sh` checks the rules marked ✔.

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

## Narrow widths: reflow, never squash

The artifact iframe is often phone-width.

- ✔ Grids start at one column: `grid-cols-1 md:grid-cols-2`. Same for flex rows: `flex-col md:flex-row`.
- ✔ No fixed `px`/`vw` widths on content. Use `max-w-*` plus `w-full`.
- ✔ Wide content (tables, code, diagrams, mockups) goes in `<div className="w-full min-w-0 overflow-x-auto">`. The page itself never scrolls sideways.
- Padding and type step down: `p-4 md:p-8`, `text-3xl md:text-5xl`.
- Side-by-side comparisons stack below `md`. Sticky or fixed elements are `hidden lg:block`.
- A flex component never goes inside running prose; it breaks line wrapping. Inline elements only.
- RoughNotation detaches inside the page's scroll container, so use `<Mark>`.
