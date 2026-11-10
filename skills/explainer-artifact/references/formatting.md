# Formatting

How each kind of content goes on the page. Component APIs: `$WAB/references/kit.md`.

## Before → after: one example, compact

Show the change on **one concrete case** (the page's running example), not as statements about it. The reader should see the fuller picture in a glance and read the explanation last.

- `example` names the case in a few words: "Ido: one person, two sign-ins".
- Each row is a short label and two **example values**: ids, chips, counts, a few words. No sentences. `<Id>` for identifiers, `<Gone>` for what no longer exists, `<Added>` for what is new, `<Chip kind="rm">` for damage done ("7 disabled"). `hint` explains an unfamiliar label in a few words ("A tenant membership").
- Both cells of a row answer the same question, so the eye compares across.
- `result` is what the reader cares about on each side ("disabled every 6 hours" / "keeps access").
- `caption` is the one-sentence description, at the end. The explanation lives there, not in the cells.
- 2–5 rows. A row that is the same on both sides stays only when it carries the point, marked `same`.
- Data changes are a before → after too: one row per table, `hint` saying what one row is, values showing what happened to the example's rows. Not a table of prose.

```tsx
<BeforeAfter
  example="Ido: one person, two sign-ins"
  rows={[
    { aspect: 'Directory', before: <><Id>Backoffice acct</Id> <Id>Platform acct</Id></>, after: <><Gone>Backoffice acct</Gone> <Id>Platform acct</Id></> },
    { aspect: 'Okta lists', before: <Id>Platform acct</Id>, after: <Id>Platform acct</Id>, same: true },
    { aspect: 'Reconcile asks', before: 'Is every account listed?', after: 'Is any account listed?' },
  ]}
  result={{ before: 'Ido disabled every 6 hours', after: 'Ido keeps access' }}
  caption="A Backoffice account never joins the directory, and the reconcile judges people, not accounts."
/>
```

## Interface changes

`<Changes>`: the name is the thing a reader looks up (`<Id>` for code names), with its `area`. `before` / `after` are a few words each, read as one line (`One unlisted account disables the person → Disabled only when no account is listed`); the one detail a reader must act on goes in `note`. Split user-facing from developer-facing with a short `<P>` above each list.

## Tables

The first column names the row in plain words; identifiers go in `<Id>`. One sentence per cell. A table that compares two options is often a `BeforeAfter` in disguise: prefer that when one side replaces the other.
