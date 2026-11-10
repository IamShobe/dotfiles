# Formatting

How each kind of content goes on the page. Component APIs: `$WAB/references/kit.md`.

## Before → after: one example, compact

Show the change on **one concrete case** (the page's running example), not as statements about it. The reader should see the fuller picture in a glance and read the explanation last.

- `example` names the case in a few words: "Ido: one person, two sign-ins".
- Each row is a short label and two **example values**: ids, chips, counts, a few words. No sentences. Use `<Id>` for identifiers and `<Gone>` for what no longer exists.
- Both cells of a row answer the same question, so the eye compares across.
- `result` is what the reader cares about on each side ("disabled every 6 hours" / "keeps access").
- `caption` is the one-sentence description, at the end. The explanation lives there, not in the cells.
- 2–4 rows. A row that is the same on both sides stays only when it carries the point.

```tsx
<BeforeAfter
  example="Ido: one person, two sign-ins"
  rows={[
    { aspect: 'Directory', before: <><Id>Backoffice acct</Id> <Id>Platform acct</Id></>, after: <><Gone>Backoffice acct</Gone> <Id>Platform acct</Id></> },
    { aspect: 'Okta lists', before: <Id>Platform acct</Id>, after: <Id>Platform acct</Id> },
    { aspect: 'Reconcile asks', before: 'Is every account listed?', after: 'Is any account listed?' },
  ]}
  result={{ before: 'Ido disabled every 6 hours', after: 'Ido keeps access' }}
  caption="A Backoffice account never joins the directory, and the reconcile judges people, not accounts."
/>
```

## Interface changes

`<Changes>`: the name is the thing a reader looks up (`<Id>` for code names), Was / Now one sentence each. Split user-facing from developer-facing with a short `<P>` above each list.

## Tables

The first column names the row in plain words; identifiers go in `<Id>`. One sentence per cell. A table that compares two options is often a `BeforeAfter` in disguise: prefer that when one side replaces the other.
