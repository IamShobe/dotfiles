# Theme tokens — raw values

Prefer the CSS vars from `<Theme/>` (`@/theme`); these raw hexes are only for a one-off need (e.g. a `recharts` stroke that can't read a var, or a data-URI SVG). To re-skin, edit the hexes in `template/src/theme.tsx` — everything styled via the vars follows.

| var | role | light | dark |
|---|---|---|---|
| `--bg` | page background | `#fafbfb` (gray-25) | `#0e0f11` |
| `--surface` | card / surface | `#ffffff` | `#1c1e20` |
| `--border` | border | `#e3e6e8` (gray-150) | `#303336` |
| `--border-hi` | border, stronger | `#d1d5d9` (gray-250) | `#4a4e53` |
| `--ink` | text primary | `#414448` (gray-800) | `#e6e9ec` |
| `--ink-2` | text secondary | `#62676c` (gray-700) | `#b4bac1` |
| `--ink-3` | text muted | `#6f767d` (gray-650) | `#8b929b` |
| `--brand` | brand accent (indigo) | `#4f46e5` | `#8b93fa` |
| `--brand-ink` | brand emphasis | `#4338ca` | `#a6acff` |
| `--signal` | highlight (amber-500) | `#ffc533` | `#ffc533` |
| `--add` / `--rm` | diff green / red | `#1a7f52` / `#c2415a` | `#4ddca0` / `#f2879f` |
| `--code-bg` / `--code-ink` | code block | `#1a1d23` / `#e6e8ef` | `#0a0b0d` / `#dfe3ee` |

**Contrast is part of the palette.** Every text and accent token clears 4.5:1 on its own `--surface` in both themes, and `--surface` sits a visible step off `--bg` so cards read without leaning on `--border`. If you re-skin, re-measure — a brand hue that looks fine on white usually fails on a dark surface (the shipped indigo had to lift from `#6366f1` to `#8b93fa` for exactly that reason).

Editing the palette itself → edit `template/src/theme.tsx` (single source of truth).

## diagram-design → explainer vars

`diagram-design` names colors by semantic role and resolves them from its own `style-guide.md`. It ships both a light and a dark skin, but a generated diagram bakes **one** skin's hexes into the SVG — so an un-rewritten diagram is stuck in whichever mode it was drawn for. Rewrite the hexes to explainer vars and it follows the page instead.

Run this over the extracted SVG (`sed -i ''` on macOS), then verify both themes:

| diagram-design role | default hex (light skin) | → replace with |
|---|---|---|
| `paper` | `#f5f5f5` | `var(--surface)` |
| `paper-2` | `#ececec` | `var(--bg)` |
| `ink` | `#2d3142` | `var(--ink)` |
| `muted` | `#4f5d75` | `var(--ink-2)` |
| `soft` | `#7a8399` | `var(--ink-3)` |
| `rule` | `rgba(45,49,66,0.12)` | `var(--border)` |
| `rule-solid` | `#bfc0c0` | `var(--border-hi)` |
| `accent` | `#eb6c36` | `var(--brand)` |
| `accent-tint` | `rgba(235,108,54,0.08)` | `var(--brand-soft)` |
| `link` | `#2e5aa8` | `var(--brand-ink)` |

Two gotchas:

- **`<marker>` fills don't inherit.** The three arrow markers (`arrow`, `arrow-accent`, `arrow-link`) carry their own `fill` — rewrite those too, or every arrowhead stays tangerine in dark mode while its line turns indigo.
- **`fill="none"` and opacity-derived fills** (`ink @ 0.05`, `ink @ 0.03`) are `rgba()` of the ink hex, not the flat hex. Rewrite them to `color-mix(in srgb, var(--ink) 5%, transparent)` or leave them — low-alpha ink reads acceptably in both themes.

The cleaner alternative, if you're generating several diagrams for one page: save a `diagram-design` profile whose tokens already **are** the explainer hexes (`/diagram-design:profile`), so the light skin lands correct with no rewrite — you still rewrite for dark-mode support.
