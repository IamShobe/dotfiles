---
name: web-artifacts-builder
description: Build claude.ai HTML artifacts from a React + Tailwind + shadcn template with a page kit, a theme design system, a themed diagram renderer and a one-call build+verify. Use for interactive or multi-section artifacts needing state, charts, diagrams or components — not a trivial single-file snippet.
license: Complete terms in LICENSE.txt
---

# Web Artifacts Builder

React + TS + Tailwind + shadcn/ui (41 components) + rich libs → one self-contained `bundle.html` (all JS/CSS inlined; CSP-safe, no CDN/eval) via Vite in ~0.6s.

**Render `<Theme/>` once near the root of every `App.tsx`:** `import { Theme } from '@/theme'` then `<Theme/>` as the first element. It's what actually switches light/dark (via `prefers-color-scheme` + `[data-theme]`) and is what shadcn's `bg-primary`/`text-muted-foreground`/etc. classes now resolve through. `index.css` only ships static light-mode fallback hex so the page isn't broken for the instant before mount — it is not a substitute and never switches themes on its own.

## Build — one call

The bottleneck is agent round-trips, not the build. Minimize turns:

```bash
bash scripts/build.sh <name> App.tsx [--specs specs.json] [--repo <checkout>]   # render diagrams, bundle, verify → <name>.html
bash scripts/build.sh <name>                                                    # rebuild after editing <name>/src/App.tsx
```

Publish `<name>.html` with the Artifact tool (the published file's basename is the gallery title, so never `bundle.html`). Re-publish the same path on edits to keep the URL. `scripts/make-artifact.sh <name> [App.tsx | -]` is the bare bundle step, without diagrams or verify.
Node missing (bare shell): `export PATH="$(dirname "$(mise which node)"):$PATH"`. First run on a machine: `eval "$(bash scripts/ensure-deps.sh)"` installs the template packages and finds diagram-design.

**Document title** (browser tab + Artifact gallery name). Put a `@title` comment on its own line in `App.tsx` — the build stamps it into `index.html` on every run:

```tsx
// @title: Billing Data Model — Review
export default function App() { … }
```

Without it the title falls back to `<name>`, so pick a human-readable `<name>` (`billing-review`, not `demo`). Never leave the placeholder `__ARTIFACT_TITLE__` in `template/index.html` hardcoded to a real name — every future artifact inherits it.

## Building blocks

- **Page kit** (`@/kit`, shipped in the template): `Page` (hero, theme, scroll container, TOC), `Section`, text (`P`, `Term`, `Id`, `Src`, `Mark`, `Chip`, `Gone`) and blocks (`BeforeAfter`, `Changes`, `Deprecations`, `Table`, `Card`, `Grid`, `Callout`, `Code`, `Steps`, `Figure`). Read `references/kit.md` before writing `App.tsx`; prefer the kit over hand-written JSX.
- **Design system**: theme vars, colors, contrast, narrow-width rules → `references/design.md` (rules for any custom JSX) and `references/theme-tokens.md` (raw values; the palette lives in `template/src/theme.tsx`).
- **Diagrams**: `references/diagram-types.md` is the catalog (which type answers which question). ⚙ types render from a JSON spec: `python3 scripts/diagrams/render.py --example <type>`, then pass the specs to `build.sh --specs`. ✎ types are drawn by hand following `references/diagram-brief.md` and converted with `scripts/diagram-to-jsx.sh <name> <files>`, which maps every color to the theme vars.
- **Verify**: `build.sh` ends with `scripts/verify.sh <name> [repo]`: theme-only colors, no shadows, responsive grids, title, `<Src>` links resolve, `<Term>` order, overflow and tiny text at 390/768/1280px, one light+dark contact sheet. Fix every ✗ in one pass.

## Rich libraries (pre-installed; import directly, Vite inlines them)

Reach for one only when it beats plain JSX; unused imports tree-shake out. **Before using any lib, read its row in `references/libraries.md`** — per-lib best practices (theme-aware colors, the common gotcha, when *not* to use it).

| Need | Import |
|---|---|
| Highlight/circle/underline a phrase | `react-rough-notation` → `RoughNotation` |
| Hover tooltip (wrap a `<span>`) | `@tippyjs/react` → `Tippy` + `import 'tippy.js/dist/tippy.css'` |
| Syntax-highlighted code | `prism-react-renderer` → `Highlight, themes` |
| Charts | `recharts` (wrap in `ResponsiveContainer`) |
| Flow/sequence/state diagram | `import mermaid` + render in `useEffect` (see Mermaid below) (+3MB) |
| Before/after wipe | `react-compare-slider` (img src = data-URI) |
| Staggered animation | `animejs` → `animate, stagger` |
| Hand-drawn shapes | `roughjs` → `rough` |
| Arrows between elements | `leader-line` → `LeaderLine` (imperative, init in `useEffect`) |

Icons: `lucide-react`. Brand logos: inline Simple-Icons `<svg fill="currentColor">`.
Bundle baseline ~450KB; `+recharts` ~+500KB; `import mermaid` ~+3MB.

**Mermaid:** `import mermaid`, render in a `useEffect` (native `<pre className="mermaid">` no-ops — host only scans initial static HTML). Component → `references/recipes.md`. **Authoring clear, color-coded diagrams** (4–7 nodes, `classDef` color-by-role, shapes, syntax) → `references/mermaid.md`.

## The iframe scrolls differently (critical)

The host **auto-sizes the iframe to content; the *parent* scrolls** — there's **no inner scroll viewport**. So these silently fail: `position: sticky`, `100vh`/`h-screen` pinning, `<a href="#id">` hash-jumps, `window` scroll listeners (`scrollY` stays 0), and scroll-root-autodetecting libs (`react-scrollama` was removed for this).

**Fix: make your own scroll container** — wrap the page in a `ref`'d `h-screen overflow-y-auto` div; everything inside then behaves normally. (Radix portal-based components — `Dialog`, `Sheet`, `Popover`, `DropdownMenu`, etc., which mount into `document.body` — are unaffected by this and position correctly; verified against this iframe's auto-sizing model.)
- **TOC/scrollspy:** vendored `Scrollspy` (`@/components/ui/scrollspy`) with `targetRef={scrollRef}`, `history={false}`. It's already hardened (rAF-throttled, no-op on unchanged id, settle-lock so clicks don't flash/trail). Style active jitter-free: **never change `font-weight`** (reflows the rail) — reserve bold metrics + signal with color and a `transform`-scaled dot.
- **Pinned/scrollytelling:** `position: fixed` (not sticky), inline fallback on narrow screens; drive steps with `IntersectionObserver`.

Scaffolds + jitter-free CSS: `references/recipes.md`.

## Design

Avoid "AI slop": no excessive centering, purple gradients, uniform rounded corners, or Inter. Deliberate palette/type/layout. Both themes through the theme vars (`references/design.md`). Wide content gets `overflow-x`.

## Notes

- shadcn docs: https://ui.shadcn.com/docs/components · adding a component (vendor it, no build-time network): `references/recipes.md`.
- Skip pre-publish testing (adds latency); Playwright after, only if needed.
- `new-artifact.sh` / `build-artifact-fast.sh` = clone / build separately. Template deps missing → `(cd template && pnpm install)`.
- **Stale-clone gotcha:** `make-artifact.sh <name>` skips the clone if `<name>/` exists (rebuild only). Added a file to `template/src` since? An old clone won't have it → `UNLOADABLE_DEPENDENCY`. Fix: `rm -rf <name>` and re-run.
