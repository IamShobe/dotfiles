# Formatting

How content goes on the page. Component APIs: `$WAB/references/kit.md`. Visual rules (color meaning, mono, interaction): `$WAB/references/design.md`.

## Principles

Every block passes the **glance test**: a reader who looks at it for three seconds, without reading any sentence, gets its point. The rest of this file is how.

1. **Show the example, not the statement.** A change is shown on one concrete case (the page's running example: a person, a request, a row) as it was and as it is. "Ido has two accounts; Okta lists one" beats "the reconcile compared each account against Okta".
2. **Values, not sentences.** Inside a block, a cell holds an identifier, a chip, a count or a few words: about 6 words, never a full sentence. If a cell needs a sentence, the block is the wrong shape.
3. **Outcome first, explanation last.** The reader looks for what happened (the result row, the status dot, the `→ now` side) before why. The why is one sentence at the end: the `caption` ("In short") or a `note`.
4. **Mark the difference.** Let the eye find what changed without reading: struck-out for what's gone, `+` for what's new, red chip for damage done, `same` (dimmed, `=`) for what didn't change. Rows that don't carry the point are cut, not dimmed.
5. **One shape per kind of content.** Pick the block by what the content is (table below), never a table of prose.
6. **One reading direction.** Within a block, comparisons line up so the eye moves across: before → after, was → now, left to right, same question in both cells. Two bullet lists side by side make the reader match lines by eye.
7. **Same words everywhere.** The labels in a block are the words the prose introduced (`<Term>`), so a reader never maps "directory" to "people table".

| Content | Block |
|---|---|
| A behavior, rule or state that changed | `<BeforeAfter example rows result caption>` |
| What a change does to data (rows, tables, records) | `<BeforeAfter>`, one row per table, `hint` = what one row is |
| A list of things that were added, changed or removed (config, APIs, rules) | `<Changes>` |
| Things removed or kept only as a fallback | `<Deprecations>` |
| A number that moved over time (runs, errors, latency, adoption) | `<TimeChart>` with a milestone on every change that explains a jump or a dip |
| A flow, a sequence, a lifecycle | a diagram in a `<Figure>` (`$WAB/references/diagram-types.md`) |
| Something the reader should try (pick a case, toggle a mode, click a node) | `<Playground controls>` with each chart in a `<Figure>` |
| Ordered actions (rollout, how to extend) | `<Steps>` |
| A lookup of homogeneous items with short attributes | `<Table>` |

## Before → after

- `example` names the case in a few words: "Ido: one person, two sign-ins".
- 2–5 rows. Each row is a short label (`hint` under it when the label is unfamiliar: "A tenant membership") and two example values that answer the same question.
- Diff markers inside values: `<Gone>` for what no longer exists, `<Added>` for what is new, `<Chip kind="rm">` for damage done ("7 disabled"), `<Id>` for identifiers.
- `result` is what the reader cares about on each side ("Disabled every 6 hours" / "Keeps platform access").
- `caption` is the one-sentence description, at the end.

```tsx
<BeforeAfter
  example="Ido: one person, two sign-ins"
  rows={[
    { aspect: 'Platform directory', before: <><Chip>Backoffice account</Chip><Chip>Platform account</Chip></>, after: <><Gone>Backoffice account</Gone><Chip>Platform account</Chip></> },
    { aspect: 'Okta lists', before: <Chip>Platform account</Chip>, after: <Chip>Platform account</Chip>, same: true },
    { aspect: 'Reconcile asks', before: 'Is every account listed?', after: 'Is any account listed?' },
  ]}
  result={{ before: 'Disabled every 6 hours', after: 'Keeps platform access' }}
  caption="A Backoffice account never enters the platform directory, and the reconcile judges people, not accounts."
/>
```

## Diagrams

- **The diagram tells the running example too.** Ido's two accounts as two lanes beats a generic "account → decision" flowchart: name the lanes, steps and sub-labels after the example's real things ("Platform account", "linked to Ido", "1 of 1: keeps access").
- **Pick the shape for the page, not only the question.** The page is wide: prefer left-to-right shapes (swimlane, sequence, LR flow) that fit at ~90%+ over tall top-down ones that shrink to 60% and turn labels to 7px. Heed the renderer's width warning: cut steps, fold a step into a sub-label, or split.
- **Decisions are diamonds with every branch labelled**, including the branch the example doesn't take ("Disabled once: none listed"), so the rule reads complete. Write the example onto the branch it takes ("Ido's Platform account").
- **Show the decision where it is made.** If a rule is per person, not per item, the diagram needs a lane or node for the person where the items meet.

## Time charts

- **When a number changed, show it over time.** A before/after of two numbers hides the shape: when it moved, whether it stuck, what spiked. Use bars for counts per day (stacked when the parts are systems or kinds that hand over), lines for rates and latencies.
- **Every outlier gets its reason.** A spike, a dip or a hand-over has a milestone at its date ("Engine v2 for every new run"), so the reader never asks "what happened here?". The milestone that is the story is `focal`.
- **Show the rhythm the reader would otherwise misread:** weekends (`shadeDays`), and what the count includes, in the caption ("hand-started runs and retries included").
- Enough days on each side of the change to show the before is stable: about two weeks before and after.

## Interface changes

`<Changes>`: the name is the thing a reader looks up (`<Id>` for code names) with its `area`. `before` / `after` are a few words each and read as one line ("One unlisted account disables the person → Disabled only when no account is listed"). The one detail a reader must know or act on (a required value, a startup failure) goes in `note`. Split user-facing from developer-facing with a short `<P>` above each list.

## Tables

Only for lookups: homogeneous items, 2–4 columns, a few words per cell. The first column names the row in plain words; identifiers go in `<Id>`. A column of sentences, or a table comparing an old and a new state, means it is another block from the table above.

## Before you publish

Look at every block in the contact sheet (or a screenshot) and apply the glance test. A block that needs its sentences read to make sense gets reshaped, not reworded.
