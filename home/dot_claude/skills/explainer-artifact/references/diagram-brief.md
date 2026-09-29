# Diagram brief

Everything needed to draw an explainer diagram, condensed from `diagram-design`
(v2.6, MIT, by Cathryn Lavery) with the `explainer` palette baked in. Read this
**instead of** diagram-design's SKILL.md, style guide and profile. Also read the
one `$DIAGRAM_DESIGN/references/type-<type>.md` for each diagram you draw: it
holds that type's layout grammar.

## Output

One file per diagram, `<slug>.html` (kebab-case), containing **only the `<svg>`**.
No `<html>`, no page chrome, no fonts link, no dark variant: the page provides
all of that, and `diagram-to-jsx.sh` maps these light hexes to theme vars.

```svg
<svg viewBox="0 0 1000 600" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="SLUG-title SLUG-desc">
  <title id="SLUG-title">Short subject name (≤60 chars)</title>
  <desc id="SLUG-desc">One sentence on what it shows, in content terms, not geometry.</desc>
  <defs>
    <marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#62676c"/></marker>
    <marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#4f46e5"/></marker>
    <marker id="arrow-link" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#4338ca"/></marker>
  </defs>
  <rect width="100%" height="100%" fill="#ffffff"/>
  <!-- connectors first, then nodes, then legend -->
</svg>
```

`<title>` must be the first child. `SLUG` must equal the file name. The converter runs the self-check.

## Palette (use only these)

| Role | Hex | Use |
|---|---|---|
| paper | `#ffffff` | background, node masks, label masks |
| ink | `#414448` | node names, primary strokes |
| muted | `#62676c` | default arrows, secondary text |
| soft | `#6f767d` | sublabels, arrow labels |
| rule / rule-solid | `#e3e6e8` / `#d1d5d9` | hairlines, legend separator |
| accent | `#4f46e5` | **1–2 focal elements per diagram, max** |
| accent-tint | `rgba(79,70,229,0.08)` | focal node fill |
| link | `#4338ca` | HTTP/API calls, external arrows |
| ink tints | `rgba(65,68,72,A)` | fills below |

## Nodes

| Node | Fill | Stroke |
|---|---|---|
| Focal (1–2) | accent-tint | accent |
| Backend / API / step | `#ffffff` | ink |
| Store / state | ink @ 0.05 | muted |
| External / cloud | ink @ 0.03 | ink @ 0.30 |
| Input / user | `rgba(98,103,108,0.10)` | soft |
| Optional / async | ink @ 0.02 | ink @ 0.20, dashed `4,3` |
| Boundary / security | `rgba(79,70,229,0.05)` | `rgba(79,70,229,0.50)`, dashed `4,4` |

```svg
<rect x="X" y="Y" width="W" height="H" rx="6" fill="#ffffff"/>                      <!-- opaque mask -->
<rect x="X" y="Y" width="W" height="H" rx="6" fill="FILL" stroke="STROKE" stroke-width="1"/>
<rect x="X+8" y="Y+6" width="28" height="12" rx="2" fill="none" stroke="STROKE" stroke-opacity="0.4" stroke-width="0.8"/>
<text x="X+22" y="Y+15" fill="STROKE" font-size="7" font-family="'Geist Mono', monospace" text-anchor="middle" letter-spacing="0.08em">API</text>
<text x="CX" y="CY+2" fill="#414448" font-size="12" font-weight="600" font-family="'Geist', sans-serif" text-anchor="middle">Node name</text>
<text x="CX" y="CY+18" fill="#62676c" font-size="9" font-family="'Geist Mono', monospace" text-anchor="middle">tech:port</text>
```

Type: names in Geist 12/600; technical sublabels, tags and arrow labels in Geist Mono. Mono is for technical content only.

## Connectors: six hard rules

1. **Orthogonal only.** Right angles with quarter-arc bends (`r=8`, min 6). A straight `<line>` only when both ends share x or y. No diagonals.
2. **Labels sit 6–10px off their line**, on an opaque `#ffffff` mask rect, never touching the stroke. ≤14 chars, ALL CAPS, Geist Mono 8, `#6f767d`, centered on the segment. Vertical segment → label beside it. Never `writing-mode`.
3. **No overlapping connectors.** Keep parallels ≥12px apart end to end. If two must cross, reroute; stacking means the layout is over budget.
4. **Fan attach points.** N connectors on one edge of length L attach at `L·k/(N+1)`, ≥12px apart. No shared points.
5. **Never pass behind a non-endpoint box.** Reroute. Only if geometrically unavoidable: dashed `4,3`, label near the source, arrowhead only at the true target.
6. **A label mask never overlaps a node drawn after it.** Put labels on open-canvas segments.

Arrows: default = muted + `url(#arrow)`; headline path = accent + `url(#arrow-accent)`; HTTP/external = link + `url(#arrow-link)`; optional/return/async = dashed `5,4`. Draw connectors before nodes.

## Layout

- **4px grid for everything**: coords, sizes, gaps (20/24/32/40/48), padding (8/12/16), radius (4/6/8).
- **Direction**: left-to-right by default, since the page is wide and short diagrams scan better. Top-down only for inherently vertical types (tree, org chart, layer stack), even where a type reference prefers top-down.
- **Budget per diagram**: ≤9 nodes, ≤12 arrows, ≤2 accent elements (accent nodes **and** accent arrows both count). Sequence: ≤5 lifelines, ≤1 fragment. Over budget → split into overview + detail, or cut.
- **Legend**: a horizontal strip at the bottom under a `#e3e6e8` hairline, "LEGEND" in Geist Mono 8. Add ~60px to the viewBox height. Never inside the diagram area.
- **Crop the viewBox to the content**: ~32px margin on every side, no empty header band (the page supplies the title). Wide viewBox (~1000 × 300–600) suits the page. The converter keeps `viewBox` and scrolls below 640px.

## Pick the type

| Showing… | Type (`type-<name>.md`) |
|---|---|
| Components and connections | `architecture` |
| Decision logic with branches | `flowchart` |
| Time-ordered messages between actors | `sequence` |
| States, transitions, guards | `state` |
| Who does what at each pipeline step | `data-flow` |
| Stacked abstraction levels / where controls live | `layers` |
| What depends on what (fan-in, cycles) | `dependency` |
| Entities and relationships / physical tables | `er` / `db-schema` |
| Where software runs | `deployment` |
| Cross-team process with handoffs | `swimlane` |
| Events in time / phased rollout | `timeline` / `gantt` |
| Parent → children | `tree` |

Other types exist (`ls $DIAGRAM_DESIGN/references/type-*.md`); an explainer rarely needs them. If a 3-column table says the same thing, use the table.

## Slop to avoid

Identical boxes for every node · accent on more than 2 things · shadows · radius over 10 · legend inside the diagram · labels without masks · mermaid-style auto-layout spacing.
