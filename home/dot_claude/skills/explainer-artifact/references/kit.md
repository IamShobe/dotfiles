# Kit API (`import { … } from '@/explainer'`)

`build.sh` installs the kit. Every component is theme-driven, reflows below `md`, and scrolls wide content in its own box. Prefer these over hand-written JSX. For anything custom, follow `references/design.md`.

## Shell

```tsx
<Page meta={meta} eyebrow="PR #412 · merged" title="Perimeters no longer need a provider"
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

## Blocks

| Component | Props |
|---|---|
| `<BeforeAfter before={…} after={…} beforeLabel? afterLabel? />` | The core shift. Stacks below md. |
| `<Card label? title? accent?>` | Surface card. `accent` = the focal one. |
| `<Grid cols={2 \| 3 \| 4}>` | Responsive card grid, one column below md. |
| `<Callout title?>` | One "why this matters" per section at most. |
| `<Code code lang? title? mark={[lines]} />` | Code block. `mark` highlights 1-based lines. |
| `<Table columns rows mono={[0]} />` | Generic table. `mono` = identifier columns. |
| `<Changes rows={[{ name, before?, after?, note? }]} />` | Interface changes. Only `after` = added, only `before` = removed. |
| `<Deprecations removed={[{what, why}]} kept={[{what, why}]} />` | Gone for good vs kept as fallback. |
| `<Steps items={[{ title, body?, code?, lang? }]} />` | Numbered how-to. |
| `<Figure caption?>` | Frame for a converted diagram: `<Figure><Pipeline /></Figure>`. |
