# Mermaid — clear, color-coded diagrams

Render it yourself (component in `recipes.md` — the native `<pre className="mermaid">` no-ops in a bundled app). This file is how to author a diagram that's *readable and color-coded*, not just valid.

## Non-negotiables for clarity

- **4–7 nodes.** If it needs more, split into two diagrams or use a subgraph. A wall of boxes explains nothing.
- **Color-code by role, not decoration.** Every fill means something (source / transform / output / deprecated). Legend it in the surrounding prose, not inside the graph.
- **Direction matches the story:** `LR` for a pipeline/flow, `TD` for a hierarchy/decision tree.
- **Shape encodes kind:** rectangle = step, `{decision}` = branch, `[(cylinder)]` = data/store, `{{hexagon}}` = external/matcher. Be consistent.
- **Label edges** when the relationship isn't obvious (`-->|resolves|`).
- Init with `securityLevel: 'loose'` (needed for `<br/>` in labels) and `theme: 'base'` so your `classDef` colors aren't overridden.

## Color-coding — `classDef` + `:::`

Define a class per role, assign with `:::`. Use the theme tokens as literal hex (mermaid can't read CSS vars):

```
flowchart LR
  A["rules.yaml<br/>rule registry"]:::src --> B["rule:<br/>MATCH_BY_TAG"]:::rule
  B --> M{{"matcher<br/>resolves at eval time"}}:::ext
  A -. tag set .-> M
  M --> P["result node<br/>id · scope"]:::out
  P --> V1["Detail page"]:::view
  P --> V2["Overview map"]:::view

  classDef src  fill:#eef2ff,stroke:#4f46e5,color:#414448
  classDef rule fill:#ffffff,stroke:#d1d5d9,color:#414448
  classDef ext  fill:#fff0cc,stroke:#ffc533,color:#414448
  classDef out  fill:#e7f6ee,stroke:#1a7f52,color:#414448
  classDef view fill:#f6f7f7,stroke:#c8cdd2,color:#414448
```

Palette to reuse (matches the shipped `theme.tsx`, light-mode readable): brand `#4f46e5`/soft `#eef2ff` · signal `#ffc533`/soft `#fff0cc` · add `#1a7f52`/soft `#e7f6ee` · neutral stroke `#d1d5d9`/fill `#f6f7f7` · ink `#414448`. Always set `color:` so label text stays legible on the fill.

## Syntax cheatsheet (from mermaid.js.org)

- **Node shapes:** `A[rect]` `A(rounded)` `A([stadium])` `A[[subroutine]]` `A[(cylinder)]` `A((circle))` `A{decision}` `A{{hexagon}}`
- **Edges:** `A --> B` (arrow) · `A --- B` (open) · `A -.-> B` (dotted) · `A ==> B` (thick) · labels: `A -->|text| B`, dotted-with-text `A -. text .-> B` (spaces required)
- **Style one node inline:** `style A fill:#eef2ff,stroke:#4f46e5,stroke-width:2px`
- **Reusable class:** `classDef name fill:…,stroke:…,color:…;` then `class A,B name;` or `A:::name`
- **Subgraph:** `subgraph id[Title]` … `end`, optional inner `direction TD`
- **Direction:** `LR` `RL` `TD`/`TB` `BT`

## Rules that avoid a broken graph (mermaid fails the whole diagram on one error)

- Quote labels with spaces/punctuation/`<br/>`: `A["App.tsx<br/>(you write)"]`. Unquoted `( [ : #` break the parser.
- One edge per line. Dotted-with-text needs the spaces: `A -. label .-> B`.
- Unique diagram `id` per `Mermaid` instance.
- `<br/>` line-breaks in labels require `securityLevel: 'loose'`.
