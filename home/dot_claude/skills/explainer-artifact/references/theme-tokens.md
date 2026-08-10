# Theme tokens — raw values

Prefer the CSS vars from `<Theme/>` (`@/theme`); these raw hexes are only for a one-off need (e.g. a `recharts` stroke that can't read a var, or a data-URI SVG). To re-skin, edit the hexes in `template/src/theme.tsx` — everything styled via the vars follows.

| var | role | light | dark |
|---|---|---|---|
| `--bg` | page background | `#fafbfb` (gray-25) | `#101112` (gray-950) |
| `--surface` | card / surface | `#ffffff` | `#181a1b` (gray-925) |
| `--border` | border | `#e3e6e8` (gray-150) | `#27282b` (gray-875) |
| `--border-hi` | border, stronger | `#d1d5d9` (gray-250) | `#51565a` (gray-750) |
| `--ink` | text primary | `#414448` (gray-800) | `#dadde1` (gray-200) |
| `--ink-2` | text secondary | `#62676c` (gray-700) | `#c8cdd2` (gray-300) |
| `--ink-3` | text muted | `#828990` (gray-600) | `#939aa2` (gray-550) |
| `--brand` | brand accent (indigo) | `#4f46e5` | `#6366f1` |
| `--brand-ink` | brand emphasis | `#4338ca` | `#818cf8` |
| `--signal` | highlight (amber-500) | `#ffc533` | `#ffc533` |
| `--add` / `--rm` | diff green / red | `#1a7f52` / `#c2415a` | `#4ddca0` / `#f2879f` |
| `--code-bg` / `--code-ink` | code block | `#1a1d23` / `#e6e8ef` | `#0b0d10` / `#dfe3ee` |

Editing the palette itself → edit `template/src/theme.tsx` (single source of truth).
