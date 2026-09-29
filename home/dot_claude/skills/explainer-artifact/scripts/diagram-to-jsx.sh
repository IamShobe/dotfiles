#!/usr/bin/env bash
# Extract the first <svg> from a diagram-design HTML export and emit a
# theme-aware React component at src/diagrams/<name>.tsx.
#
#   diagram-to-jsx.sh <diagram.html> <name> [outdir]
#
# Assumes the diagram was generated under the `explainer` diagram-design
# profile, so its hexes are already the explainer light-theme values; those are
# rewritten to CSS vars here so the diagram tracks dark mode too.
set -euo pipefail

SRC="${1:?usage: diagram-to-jsx.sh <diagram.html> <name> [outdir]}"
NAME="${2:?missing <name>}"
OUTDIR="${3:-src/diagrams}"
[ -f "$SRC" ] || { echo "no such file: $SRC" >&2; exit 1; }
[[ "$NAME" =~ ^[a-zA-Z][a-zA-Z0-9-]*$ ]] || { echo "bad name: $NAME" >&2; exit 1; }

COMPONENT="$(python3 -c "
import sys,re
n=sys.argv[1]
print(''.join(w.capitalize() for w in re.split(r'[-_]',n)))
" "$NAME")"

mkdir -p "$OUTDIR"
OUT="$OUTDIR/$NAME.tsx"

python3 - "$SRC" "$OUT" "$COMPONENT" <<'PY'
import re, sys
src, out, comp = sys.argv[1], sys.argv[2], sys.argv[3]
html = open(src, encoding='utf-8').read()

m = re.search(r'<svg\b.*?</svg>', html, re.S | re.I)
if not m:
    sys.exit(f'no <svg> found in {src}')
svg = m.group(0)

# explainer light-theme hex -> CSS var (marker fills included: plain text sub)
for hexv, var in [
    ('#ffffff', 'var(--surface)'), ('#fafbfb', 'var(--bg)'),
    ('#414448', 'var(--ink)'),     ('#62676c', 'var(--ink-2)'),
    ('#6f767d', 'var(--ink-3)'),   ('#e3e6e8', 'var(--border)'),
    ('#d1d5d9', 'var(--border-hi)'),
    ('#4f46e5', 'var(--brand)'),   ('#4338ca', 'var(--brand-ink)'),
    ('#ffc533', 'var(--signal)'),
]:
    svg = re.sub(hexv, var, svg, flags=re.I)
# accent-tint color-mix() -> brand-soft token
svg = re.sub(r'color-mix\(in srgb,\s*var\(--brand\)[^)]*\)', 'var(--brand-soft)', svg)

# kebab attributes -> camelCase, skipping data-*/aria-* (JSX keeps those dashed)
def camel(mo):
    a = mo.group(1)
    if a.startswith(('data-', 'aria-')):
        return mo.group(0)
    head, *rest = a.split('-')
    return ' ' + head + ''.join(p.capitalize() for p in rest) + '='
svg = re.sub(r'\s([a-zA-Z]+(?:-[a-zA-Z]+)+)=', camel, svg)

svg = re.sub(r'\bclass=', 'className=', svg)

# inline style="a:b;c:d" -> style={{a:'b',c:'d'}}
def style(mo):
    decls = [d for d in mo.group(1).split(';') if d.strip()]
    pairs = []
    for d in decls:
        if ':' not in d:
            continue
        k, v = d.split(':', 1)
        k = k.strip(); v = v.strip().replace("'", "\\'")
        head, *rest = k.split('-')
        pairs.append(f"{head + ''.join(p.capitalize() for p in rest)}: '{v}'")
    return 'style={{' + ', '.join(pairs) + '}}'
svg = re.sub(r'style="([^"]*)"', style, svg)

# self-close void-ish empty tags JSX requires closing
for tag in ('path','circle','rect','line','polyline','polygon','ellipse','use','stop','image','feGaussianBlur','feOffset','feMerge','feMergeNode','feFlood','feComposite'):
    svg = re.sub(rf'<{tag}\b([^>]*?)(?<!/)>', rf'<{tag}\1 />', svg)
svg = re.sub(r'\s+/>', ' />', svg)

# HTML comments -> JSX comments (a bare <!-- --> is a syntax error in JSX)
svg = re.sub(r'<!--(.*?)-->', lambda mo: '{/*' + mo.group(1).replace('*/', '* /') + '*/}', svg, flags=re.S)

# full-content-width sizing; keep viewBox/title/desc untouched
for _ in range(2):
    svg = re.sub(r'<svg\b([^>]*?)\s(?:width|height)="[^"]*"', r'<svg\1', svg, count=1)
svg = re.sub(r'<svg\b', '<svg className="w-full h-auto" style={{minWidth: 640}}', svg, count=1)

body = '\n'.join('      ' + l if l.strip() else '' for l in svg.splitlines())
open(out, 'w', encoding='utf-8').write(
    f"export function {comp}() {{\n"
    f"  return (\n"
    f'    <div className="w-full overflow-x-auto">\n'
    f"{body}\n"
    f"    </div>\n"
    f"  );\n"
    f"}}\n"
)
print(f'wrote {out}')
PY

# report anything still hardcoded
if grep -oE '#[0-9a-fA-F]{6}' "$OUT" | sort -u | grep -q .; then
  echo "note: unmapped hexes remain in $OUT (check against references/theme-tokens.md):" >&2
  grep -oE '#[0-9a-fA-F]{6}' "$OUT" | sort -u | sed 's/^/  /' >&2
fi
echo "import { $COMPONENT } from '@/diagrams/$NAME';"
