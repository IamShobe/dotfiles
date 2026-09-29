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

## Diagrams

`scripts/diagram-to-jsx.sh` maps every diagram color to these vars: the explainer profile's hexes, diagram-design's default skin, and their `rgba()` tints, marker fills included. That's why a converted diagram follows light/dark on its own. Don't hand-edit colors in `src/diagrams/`. To support a new palette color, add it to the `HEX` / `RGB` tables in the converter, once, for every future diagram.
