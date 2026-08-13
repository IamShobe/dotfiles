# Rich libraries — best practices

How to use each pre-installed lib *well*. Read the row you need. All bundle inline (CSP-safe); import only what you reference (tree-shaken). Style everything through the theme vars from `<Theme/>` (`@/theme`) so both light/dark work — never hardcode a hex that a var already covers.

**Overlay libs + custom scroll containers, as a rule:** `react-rough-notation`, `leader-line`, and anything else that draws an absolutely-positioned overlay sized at mount (not real DOM flow) has no listener on an arbitrary scrollable ancestor — only on `window` resize/scroll. Inside this template's `ref`'d `overflow-y-auto` scroll container (used for the TOC pattern, see `recipes.md`), the overlay's position goes stale the instant that div scrolls: the mark/arrow visibly detaches from what it's annotating. Safe only when the page's scroll container is the window itself (no wrapping `overflow-y-auto` div). Otherwise, prefer a same-flow alternative (a plain CSS-styled `<span>` for emphasis, an inline SVG arrow instead of `LeaderLine`) so the effect scrolls with its target instead of floating over it.

## recharts (charts)

Reach for it only when a number genuinely needs a shape — a 3-row comparison is a better table. When you do:
- Always wrap in `<ResponsiveContainer>` with a **fixed-height parent** (`<div className="h-56">`), or it collapses to 0.
- Theme-aware: axis/label `fill`, grid `stroke`, series `stroke`/`fill` must be literal colors (recharts can't read CSS vars). Pull them from `references`/`theme-tokens.md` and set them per-series — don't rely on recharts defaults (they clash with the palette).
- `<Bar>`/`<Line>` `isAnimationActive={show}` gated on a mount flag for one clean entrance; kill animation on re-render.
- Kill chartjunk: `<XAxis tickLine={false} axisLine={false}>`, no default gridlines unless they aid reading, `<Tooltip>` only if the exact value matters.
- Log scale (`scale="log"`) when one bar dwarfs the rest; say so in a caption.

## @tippyjs/react (tooltips)

- Wrap a real element, and for a plain inline target wrap a `<span>` (Tippy needs a ref-able child; a fragment/text errors).
- `import 'tippy.js/dist/tippy.css'` once. `delay={[80,0]}` feels responsive without flicker.
- Tooltips are progressive disclosure — the page must read fully without ever hovering. Never hide load-bearing info in one.
- Keep content short (a phrase); for rich content use a popover pattern, not a paragraph in a tooltip.

## react-rough-notation (emphasis)

- **Never inside a custom scroll container** (a `ref`'d `div` with `overflow-y-auto`, e.g. the TOC scroll-container pattern above). RoughNotation draws an absolutely-positioned SVG sized once on mount/window-resize; it has no listener on an arbitrary scrollable ancestor, so the mark stays pinned to its mount-time viewport position and visibly detaches from the text as soon as that div scrolls. Symptom: a highlight/circle floating away from its word during scroll. If the page's scroll container is the `<body>`/window (no wrapping `overflow-y-auto` div), it's safe. Otherwise use a plain CSS emphasis instead (e.g. `<span style={{ background: "var(--signal)", padding: "0 0.3em", borderRadius: "2px" }}>`), which scrolls with the text because it's part of normal flow, not an overlay.
- One, maybe two annotations per page. It's a spotlight; more than that and nothing stands out.
- Gate `show` on a mount flag + small `setTimeout` so it animates in after paint (annotating before layout settles mis-draws).
- `type`: `highlight` for a phrase, `underline`/`circle` for a term, `strike` for removed. Color from `--signal` (highlight) or `--brand`.
- Wrap the smallest span that carries the meaning, not a whole sentence.

## prism-react-renderer (code)

- Render-prop API: map `tokens` → lines → `getTokenProps`. Pick a `theme` from `themes` that fits light/dark, or override token colors to the palette.
- For a few before/after lines, hand-rolled colored `<span>`s are lighter than pulling Prism — use Prism when the block is real, multi-line source.
- Put the code in its own `overflow-x-auto` container; never let it widen the page.

## mermaid (diagrams)

See `references/mermaid.md` — color-code by role via `classDef`, 4–7 nodes, render-it-yourself component. The single biggest quality lever is the color legend, not the topology.

## animejs v4 (motion)

- Named exports: `import { animate, stagger } from 'animejs'` (v4 — not a default import).
- Use it for **one** orchestrated moment (a staggered reveal of a row of cards on mount), not ambient motion everywhere — scattered animation reads as AI slop.
- `animate(targets, { opacity:[0,1], translateY:[8,0], delay: stagger(120), duration:500, ease:'out(3)' })`.
- Respect `prefers-reduced-motion` (the theme's reduced-motion rule already disables CSS animation; guard JS animation too).

## react-compare-slider (before/after wipe)

- Only for genuinely *visual* before/after (a UI screenshot, a rendered mockup). For text/code before/after use two cards or a diff — a slider over text is a gimmick.
- Images must be **data-URIs** (CSP blocks remote); inline SVG via `ReactCompareSliderImage src="data:image/svg+xml,…"` works well for hand-drawn mockups.
- Give it explicit width/height or it collapses.

## roughjs (hand-drawn shapes)

- Draw onto a canvas/svg ref in `useEffect`. Its charm is a deliberate hand-drawn feel — use for an informal/sketch diagram, not a precise system diagram (mermaid is better there).
- One visual language per page: don't mix rough.js sketchiness with crisp shadcn cards unless the contrast is the point.

## leader-line (arrows between elements)

- Imperative + DOM-mutating: create in `useEffect` **after** layout, store the instance, `.remove()` on cleanup, and reposition on resize (`new LeaderLine(startEl, endEl)`).
- Fragile inside scroll/transform containers — it positions with absolute overlays. Prefer an inline SVG arrow or a mermaid edge unless you specifically need arrows between existing DOM nodes.

## Icons

- `lucide-react` for UI glyphs: `import { Zap } from 'lucide-react'`, size via `className="size-4"`, color via `currentColor` (inherits `--ink`/`--brand`).
- Brand logos: inline a Simple-Icons `<svg>` path with `fill="currentColor"` or the brand hex — never a remote `<img>` (CSP), never a placeholder glyph.

## Cross-cutting

- **Default to zero-lib.** shadcn + Tailwind + the theme vars cover most explainers. Add a lib only where it lands the message better than plain JSX, per-section.
- **Size:** baseline ~450KB; `+recharts` ~+500KB; `import mermaid` ~+3MB. Note the cost before importing a heavy one.
- **Never `flex`/`inline-flex` on a component meant to sit inline in running prose** (an icon+link, an icon+badge dropped mid-sentence — e.g. a `SourceLink`-style "icon + label" link). A flex box doesn't participate in normal inline text reflow the way `inline` does; at the exact point a line wraps next to it, the whitespace around it can collapse or misplace, producing a visible glued-together artifact (`fails with⇄clear message`). Symptom is subtle and only shows at certain wrap widths, easy to miss in a quick check. Fix: keep the wrapping element `inline` (an `<a>`/`<span>`'s default), and lay out the icon+text pairing with `inline-block` + `align-[-2px]` (or similar baseline nudge) on the icon plus a small `mr-1`, not `display:flex`. Reserve `flex`/`inline-flex` for block-level layout (a card, a row of badges, a page shell) — never for something a sentence flows around.
- **Theme first:** every color you pass a lib should trace to a token, so re-skinning `theme.tsx` re-skins the charts/annotations too.
