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
- `group="…"` on consecutive sections makes them one numbered part: the rail shows the part with its sections indented and lights up the part being read, and the page shows a "Part N · …" divider. Below lg, where the rail is hidden, the hero gets one collapsed "Contents" line instead.
- `Page` renders `<Theme/>`, the fonts, the scroll container and the hero. Don't add them yourself.

## Text

| Component | Use |
|---|---|
| `<P>` | Body paragraph, capped at 88ch. Keep it to 3 lines or fewer. |
| `<Term def="plain-words definition">word</Term>` | **First** use of any new word. After that, use the bare word. |
| `<Id>fetchUser()</Id>` | Inline identifier. |
| `<Mark>` | Highlight a phrase (instead of RoughNotation). |
| `<Src path="src/a.ts" lines="12-24" />` | Commit-pinned permalink. Inline, safe in prose. Falls back to plain code with no remote. |
| `<Ref href>` | A link to where a reference lives (ticket, PR, issue, doc): `<Ref href="https://…/pull/42">repo#42</Ref>`. Opens in a new tab. |
| `<Chip kind="add \| rm \| change \| keep \| neutral">` | Diff chip or pill. |
| `<Gone>` / `<Added>` | Something that no longer exists (red, struck) / is new (green, +), inside an example value. |

## Blocks

| Component | Props |
|---|---|
| `<Tldr items={[{ label, statement, facts?, tone? }]} />` | The page at a glance: one row per question, a colored label, a short `statement` and its numbers as `facts` pills. `tone`: `problem` `change` `result` `action` `neutral`. |
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
| `<Figure caption?>` | Frame for any diagram or chart (SVG or HTML), built on `react-zoom-pan-pinch`: fitted to the width and 70% of the screen height, an always-visible zoom bar (−, fit %, +, fullscreen), ctrl/⌘ + wheel or pinch to zoom, drag to pan within bounds, double-click to toggle, arrow keys, Esc leaves fullscreen. A rendered diagram's legend is lifted out of the zoomable drawing and pinned beside the zoom bar. |
| `<TimeChart data={[{ date: 'YYYY-MM-DD', …series }]} series={[{ key, label, tone }]} kind="bar\|line" stacked? milestones={[{ date, label, focal? }]} shadeDays={[5, 6]} yLabel caption />` | Values over time with the events that explain them: one slot per day, numbered milestone markers with a key underneath (labels never collide), shaded weekdays, a tooltip with the day's values and events, theme colors in both modes. `tone`: `brand` `signal` `muted` `add` `rm` `ink`. |
| `<Playground controls={…}>{charts}</Playground>` | Interactive widget: the controls column stays in view (sticky, pinned on top below lg) while the reader scrolls and zooms the charts. Put each chart in a `<Figure>`. |

