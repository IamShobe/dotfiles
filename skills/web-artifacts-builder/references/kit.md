# Kit API (`import { … } from '@/kit'`)

The template ships the kit at `src/kit`. Every component is theme-driven, reflows below `md`, and scrolls wide content in its own box. Prefer these over hand-written JSX. For anything custom, follow `references/design.md`.

## Shell

```tsx
<Page meta={meta} eyebrow="PR #412 · merged" title="Projects no longer need an owner"
      thesis="One sentence a non-author understands." pills={['api', 'db migration']}>
  <Section id="shift" title="The core shift" takeaway="The one line a skimmer must get.">…</Section>
  …
</Page>
```

- `meta` = the `meta` line from `gather-facts.sh`. It drives every `<Src>` link.
- `<Section>`s must be **direct children** of `<Page>`. The TOC rail is built from them and appears at `lg` when there are 3 or more.
- `Page` renders `<Theme/>`, the fonts, the scroll container and the hero. Don't add them yourself.

## Text

| Component | Use |
|---|---|
| `<P>` | Body paragraph, capped at 88ch. Keep it to 3 lines or fewer. |
| `<Term def="plain-words definition">word</Term>` | **First** use of any new word. After that, use the bare word. |
| `<Id>fetchUser()</Id>` | Inline identifier. |
| `<Mark>` | Highlight a phrase (instead of RoughNotation). |
| `<Src path="src/a.ts" lines="12-24" />` | Commit-pinned permalink. Inline, safe in prose. Falls back to plain code with no remote. |
| `<Chip kind="add \| rm \| change \| keep \| neutral">` | Diff chip or pill. |
| `<Gone>` / `<Added>` | Something that no longer exists (red, struck) / is new (green, +), inside an example value. |

## Blocks

| Component | Props |
|---|---|
| `<BeforeAfter example rows={[{ aspect, hint?, before, after, same? }]} result={{ before, after }} caption beforeLabel? afterLabel? />` | Old → new on one concrete example: a compact card, one row per aspect (`hint` = small line under the label, `same` = unchanged: dimmed, `=` on the seam, hideable), a ✗/✓ verdict row, an "In short" caption. Stacks below md. |
| `<BeforeAfter before={…} after={…} caption? />` | Free-form old → new, for what doesn't split into rows (a mockup, a screenshot). |
| `<Changes rows={[{ name, area?, before?, after?, note? }]} />` | Compact changelog: status dot, name + area (`config` `behavior` `data` `api` `ui` `access`, each with an icon), `was → now` inline, `note` small underneath. Only `after` = added, only `before` = removed. |
| `<Deprecations removed={[{what, why}]} kept={[{what, why}]} />` | Gone for good vs kept as fallback. |
| `<Card label? title? accent?>` | Surface card. `accent` = the focal one. |
| `<Grid cols={2 \| 3 \| 4}>` | Responsive card grid, one column below md. |
| `<Callout title?>` | One "why this matters" per section at most. |
| `<Code code lang? title? mark={[lines]} />` | Code block. `mark` highlights 1-based lines. |
| `<Table columns rows mono? />` | Generic table. The first column names each row. `mono` = columns holding only identifiers; otherwise wrap identifiers in `<Id>`. |
| `<Steps items={[{ title, body?, code?, lang? }]} />` | Numbered how-to. |
| `<Figure caption?>` | Frame for any diagram or chart (SVG or HTML), built on `react-zoom-pan-pinch`: fitted to the width and 70% of the screen height, an always-visible zoom bar (−, fit %, +, fullscreen), ctrl/⌘ + wheel or pinch to zoom, drag to pan within bounds, double-click to toggle, arrow keys, Esc leaves fullscreen. |
| `<Playground controls={…}>{charts}</Playground>` | Interactive widget: the controls column stays in view (sticky, pinned on top below lg) while the reader scrolls and zooms the charts. Put each chart in a `<Figure>`. |

