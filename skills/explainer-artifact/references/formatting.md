# Formatting

How content goes on the page. Component APIs: `$WAB/references/kit.md`. Visual rules (color meaning, mono, interaction): `$WAB/references/design.md`.

The examples below follow one invented running example: Sam, a customer with two saved cards, where checkout used to cancel the order when the first card failed and now tries every card.

## Principles

Every block passes the **glance test**: a reader who looks at it for three seconds, without reading any sentence, gets its point. The rest of this file is how.

1. **Show the example, not the statement.** A change is shown on one concrete case (the page's running example: a person, a request, a row) as it was and as it is. "Sam has two cards; the first is expired" beats "the payment step evaluated each stored method".
2. **Values, not sentences.** Inside a block, a cell holds an identifier, a chip, a count or a few words: about 6 words, never a full sentence. If a cell needs a sentence, the block is the wrong shape.
3. **Outcome first, explanation last.** The reader looks for what happened (the result row, the status dot, the `→ now` side) before why. The why is one sentence at the end: the `caption` ("In short") or a `note`.
4. **Mark the difference.** Let the eye find what changed without reading: struck-out for what's gone, `+` for what's new, red chip for damage done, `same` (dimmed, `=`) for what didn't change. Rows that don't carry the point are cut, not dimmed.
5. **One shape per kind of content.** Pick the block by what the content is (table below), never a table of prose.
6. **One reading direction.** Within a block, comparisons line up so the eye moves across: before → after, was → now, left to right, same question in both cells. Two bullet lists side by side make the reader match lines by eye.
7. **Same words everywhere.** The labels in a block are the words the prose introduced (`<Term>`), so a reader never maps "wallet" to "payment methods table".
8. **Every reference is a link.** A ticket, PR, issue, dashboard or doc is a `<Ref href>` to its real page; code is a `<Src>` permalink. A bare "PROJ-123" or "repo#42" is a dead end (`verify.sh` fails on it).

| Content | Block |
|---|---|
| The whole story at a glance (the first section) | `<Tldr>` (what broke, why, fix, status, what you do) + the page's main `<BeforeAfter>` |
| A behavior, rule or state that changed | `<BeforeAfter example rows result caption>` |
| What a change does to data (rows, tables, records) | `<BeforeAfter>`, one row per table, `hint` = what one row is |
| A list of things that were added, changed or removed (config, APIs, rules) | `<Changes>` |
| Things removed or kept only as a fallback | `<Deprecations>` |
| A number that moved over time (requests, errors, latency, adoption) | `<TimeChart>` with a milestone on every change that explains a jump or a dip |
| A flow, a sequence, a lifecycle | a diagram in a `<Figure>` (`$WAB/references/diagram-types.md`) |
| Something the reader should try (pick a case, toggle a mode, click a node) | `<Playground controls>` with each chart in a `<Figure>` |
| Ordered actions (rollout, how to extend) | `<Steps>` |
| A lookup of homogeneous items with short attributes | `<Table>` |

## TL;DR first, then the story

- **The first section is the TL;DR: facts, then the picture.** A `<Tldr>` answers the questions a reader comes with, one row each, in this order: *What broke* (or *What's new*), *Why*, *The fix*, *Status* (`<Ref>` links, merged vs deployed said honestly), *What you do* (the one next action, or "Nothing" plus when it resolves itself). Then the page's main `<BeforeAfter>` on the running example. No takeaway sentence and no `caption` there: the rows already say it. A reader who stops here has the full picture; every later section is the long version of one row.
- **Readable in seconds.** Write the TL;DR for a reader with no working memory to spare:
  - each `statement` is ≤ 8 plain words and leads with the outcome ("Act staff locked out", not "An issue was found where…");
  - every number, count, date and frequency moves out of the sentence into a `facts` pill ("6 people", "every 6 hours", "since Nov 4"), so the eye picks numbers up without parsing;
  - one idea per row, no em-dash clauses, no "which means";
  - the last row is the reader's next action; "Nothing" is a valid, valuable answer.
- **A document, not a pitch.** The TL;DR is dense and factual: counts, dates, names, links. Big cards, slogans and arrows between boxes are cut.
- **The TL;DR speaks plain words only.** It comes before any `<Term>`, so it uses no internal names, no acronyms and no new concepts: "stored on the platform", not "the directory". `verify.sh` fails a term used before its `<Term>`.
- **Group the rest into 3–4 parts that tell the story**, with `group` on each `<Section>`: typically *What went wrong* → *The fix* → *Shipping* → *What's next* (or *Why* → *How it works* → *What changes for you*). The rail numbers the parts and lights up the one being read. A part holds 1–3 sections.
- **Section titles say what the reader learns, in ≤ 4 words** ("How Sam's order failed", "Database changes"), so the rail reads as a table of contents of the story, not a list of headings.

```tsx
<Tldr items={[
  { label: 'What broke', tone: 'problem', statement: 'Orders cancelled with a valid card on file', facts: ['312 orders', 'since Mar 3'] },
  { label: 'Why', tone: 'neutral', statement: 'Checkout tried only the first card', facts: ['first card expired'] },
  { label: 'The fix', tone: 'change', statement: 'Checkout tries every saved card', facts: ['cancel only if all fail'] },
  { label: 'Status', tone: 'result', statement: <>✓ Merged: <Ref href="https://…/pull/42">shop#42</Ref></>, facts: ['deploys Thursday'] },
  { label: 'What you do', tone: 'action', statement: 'Nothing', facts: ['retries run on deploy'] },
]} />
```

## Readable everywhere

The TL;DR rules hold for the whole page, at a lower density: lead with the outcome, plain short sentences, numbers where the eye can find them, lists of ≤ 5 items (split longer ones into "now" and "later"), and every section's takeaway is one sentence a tired reader understands on first read. When a paragraph needs a second read, it gets shorter or becomes a block.

## Introduce before you use

Every new word (a concept, an internal name, an acronym, a renamed thing) is defined in plain words at its **first** appearance with `<Term def="…">`, before any heading, TL;DR card, diagram, table or rail entry uses it. A reader who meets a word they don't know stops reading. When the TL;DR, a diagram or a title needs the idea before its definition, say it in plain words there instead.

## Before → after

- `example` names the case in a few words: "Sam: one customer, two cards".
- 2–5 rows. Each row is a short label (`hint` under it when the label is unfamiliar: "One saved payment method") and two example values that answer the same question.
- Diff markers inside values: `<Gone>` for what no longer exists, `<Added>` for what is new, `<Chip kind="rm">` for damage done ("3 orders cancelled"), `<Id>` for identifiers.
- `result` is what the reader cares about on each side ("Order cancelled" / "Order paid").
- `caption` is the one-sentence description, at the end.

```tsx
<BeforeAfter
  example="Sam: one customer, two cards"
  rows={[
    { aspect: 'Cards tried', before: <><Chip>Expired card</Chip><Gone>Valid card</Gone></>, after: <><Chip>Expired card</Chip><Chip>Valid card</Chip></> },
    { aspect: 'Saved cards', before: <Chip>2 cards</Chip>, after: <Chip>2 cards</Chip>, same: true },
    { aspect: 'Checkout asks', before: 'Did the first card fail?', after: 'Did every card fail?' },
  ]}
  result={{ before: 'Order cancelled', after: 'Order paid' }}
  caption="Checkout now tries every saved card and cancels only when all of them fail."
/>
```

## Diagrams

- **The diagram tells the running example too.** Sam's two cards as two lanes beats a generic "payment → decision" flowchart: name the lanes, steps and sub-labels after the example's real things ("Expired card", "declined", "1 of 2: paid").
- **Pick the shape for the page, not only the question.** The page is wide: prefer left-to-right shapes (swimlane, sequence, LR flow) that fit at ~90%+ over tall top-down ones that shrink to 60% and turn labels to 7px. Heed the renderer's width warning: cut steps, fold a step into a sub-label, or split.
- **Decisions are diamonds with every branch labelled**, including the branch the example doesn't take ("Cancelled: every card failed"), so the rule reads complete. Write the example onto the branch it takes ("Sam's valid card").
- **Show the decision where it is made.** If a rule is per customer, not per card, the diagram needs a lane or node for the customer where the cards meet.

## Time charts

- **When a number changed, show it over time.** A before/after of two numbers hides the shape: when it moved, whether it stuck, what spiked. Use bars for counts per day (stacked when the parts are systems or kinds that hand over), lines for rates and latencies.
- **Every outlier gets its reason.** A spike, a dip or a hand-over has a milestone at its date ("New checkout for every order"), so the reader never asks "what happened here?". The milestone that is the story is `focal`.
- **Show the rhythm the reader would otherwise misread:** weekends (`shadeDays`), and what the count includes, in the caption ("retries included").
- Enough days on each side of the change to show the before is stable: about two weeks before and after.

## Interface changes

`<Changes>`: the name is the thing a reader looks up (`<Id>` for code names) with its `area`. `before` / `after` are a few words each and read as one line ("First failed card cancels the order → Cancelled only when every card fails"). The one detail a reader must know or act on (a required value, a startup failure) goes in `note`. Split user-facing from developer-facing with a short `<P>` above each list.

## Tables

Only for lookups: homogeneous items, 2–4 columns, a few words per cell. The first column names the row in plain words; identifiers go in `<Id>`. A column of sentences, or a table comparing an old and a new state, means it is another block from the table above.

## Before you publish

Look at every block in the contact sheet (or a screenshot) and apply the glance test. A block that needs its sentences read to make sense gets reshaped, not reworded.
