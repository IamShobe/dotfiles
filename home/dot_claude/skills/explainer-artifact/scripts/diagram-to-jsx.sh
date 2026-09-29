#!/usr/bin/env bash
# Convert diagram-design HTML files into theme-aware React components, in one call:
#
#   diagram-to-jsx.sh <artifact-dir> <diagram.html>...
#
# For each file (slug = file name without .html):
#   - runs diagram-design's self_check.py (accessible-SVG contract)
#   - extracts the first <svg>, maps every palette color to explainer CSS vars
#     (explainer profile AND diagram-design's default skin, hex and rgba), so the
#     diagram follows light/dark with no hand-editing
#   - prefixes ids per slug, so markers/patterns never collide between diagrams
#   - writes <artifact-dir>/src/diagrams/<slug>.tsx, creating the build
#     workspace first if it doesn't exist yet
# Prints one import line per diagram. Exit 1 only if a file failed.
set -euo pipefail

ART="${1:?usage: diagram-to-jsx.sh <artifact-dir> <diagram.html>...}"; shift
[ $# -gt 0 ] || { echo "usage: diagram-to-jsx.sh <artifact-dir> <diagram.html>..." >&2; exit 1; }
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "${WAB:-}" ] || [ -z "${DIAGRAM_DESIGN:-}" ]; then
  eval "$(bash "$HERE/ensure-deps.sh")"
fi
[ -d "$ART/src" ] || bash "$WAB/scripts/new-artifact.sh" "$ART" >/dev/null
OUTDIR="$ART/src/diagrams"; mkdir -p "$OUTDIR"

FAIL=0
for SRC in "$@"; do
  SLUG="$(basename "$SRC" .html)"
  if [ ! -f "$SRC" ]; then echo "✗ $SRC: no such file" >&2; FAIL=1; continue; fi
  if ! [[ "$SLUG" =~ ^[a-z][a-z0-9-]*$ ]]; then
    echo "✗ $SRC: name the file <kebab-slug>.html (got '$SLUG')" >&2; FAIL=1; continue
  fi
  if ! CHECK="$(python3 "$DIAGRAM_DESIGN/scripts/self_check.py" "$SRC" 2>&1)"; then
    echo "✗ $SRC failed diagram-design self_check — fix the source, then re-run:" >&2
    printf '%s\n' "$CHECK" | sed 's/^/    /' >&2; FAIL=1; continue
  fi
  python3 - "$SRC" "$OUTDIR/$SLUG.tsx" "$SLUG" <<'PY' || FAIL=1
import re, sys
src, out, slug = sys.argv[1:4]
m = re.search(r'<svg\b.*?</svg>', open(src, encoding='utf-8').read(), re.S | re.I)
if not m:
    sys.exit(f'✗ {src}: no <svg> found')
svg = m.group(0)

# Palette → CSS vars. Explainer profile first, then diagram-design's shipped skin,
# so even a diagram drawn with the wrong profile lands in-palette.
HEX = {
    # explainer profile (= theme.tsx light values)
    '#ffffff': 'surface', '#fafbfb': 'bg', '#414448': 'ink', '#62676c': 'ink-2',
    '#6f767d': 'ink-3', '#e3e6e8': 'border', '#d1d5d9': 'border-hi',
    '#4f46e5': 'brand', '#4338ca': 'brand-ink', '#ffc533': 'signal',
    # diagram-design default skin
    '#f5f5f5': 'surface', '#ececec': 'bg', '#2d3142': 'ink', '#4f5d75': 'ink-2',
    '#7a8399': 'ink-3', '#bfc0c0': 'border-hi', '#eb6c36': 'brand', '#2e5aa8': 'brand-ink',
}
RGB = {  # rgba() bases → the var they're a tint of
    (65, 68, 72): 'ink', (98, 103, 108): 'ink-2', (111, 118, 125): 'ink-3', (79, 70, 229): 'brand',
    (45, 49, 66): 'ink', (79, 93, 117): 'ink-2', (122, 131, 153): 'ink-3', (235, 108, 54): 'brand',
}
for h, v in HEX.items():
    svg = re.sub(re.escape(h) + r'(?![0-9a-f])', f'var(--{v})', svg, flags=re.I)
def rgba(mo):
    r, g, b, a = int(mo[1]), int(mo[2]), int(mo[3]), float(mo[4])
    v = RGB.get((r, g, b))
    return f'color-mix(in srgb, var(--{v}) {round(a*100)}%, transparent)' if v else mo[0]
svg = re.sub(r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)', rgba, svg)
svg = re.sub(r'color-mix\(in srgb,\s*var\(--brand\)\s*([1-9]|1[0-2])%,\s*transparent\)', 'var(--brand-soft)', svg)  # light tints only

# Per-diagram ids: id="arrow" → id="<slug>-arrow", plus every reference to it.
ids = {i for i in re.findall(r'\bid="([^"]+)"', svg) if not i.startswith(slug + '-')}
for i in sorted(ids, key=len, reverse=True):
    new = f'{slug}-{i}'
    svg = re.sub(rf'\bid="{re.escape(i)}"', f'id="{new}"', svg)
    svg = re.sub(rf'url\(#{re.escape(i)}\)', f'url(#{new})', svg)
    svg = re.sub(rf'href="#{re.escape(i)}"', f'href="#{new}"', svg)
    svg = re.sub(rf'(aria-(?:labelledby|describedby)="[^"]*)\b{re.escape(i)}\b', rf'\g<1>{new}', svg)

# HTML → JSX. Text first, before any JSX braces exist: drop authoring comments,
# and escape the characters JSX treats as syntax in text ("it >3 times?", "{id}").
svg = re.sub(r'<!--.*?-->', '', svg, flags=re.S)
JSX_TEXT = {'>': "{'>'}", '{': "{'{'}", '}': "{'}'}"}
svg = re.sub(r'>([^<]+)<', lambda mo: '>' + re.sub(r'[>{}]', lambda c: JSX_TEXT[c[0]], mo[1]) + '<', svg)

def camel(mo):
    a = mo.group(1)
    if a.startswith(('data-', 'aria-')):
        return mo.group(0)
    head, *rest = a.split('-')
    return ' ' + head + ''.join(p.capitalize() for p in rest) + '='
svg = re.sub(r'\s([a-zA-Z]+(?:-[a-zA-Z]+)+)=', camel, svg)
svg = re.sub(r'\sxlink:href=', ' href=', svg)
svg = re.sub(r'\bclass=', 'className=', svg)
def style(mo):
    pairs = []
    for d in mo.group(1).split(';'):
        if ':' not in d:
            continue
        k, v = d.split(':', 1)
        head, *rest = k.strip().split('-')
        pairs.append(f"{head + ''.join(p.capitalize() for p in rest)}: '{v.strip()}'".replace("\\", "\\\\"))
    return 'style={{' + ', '.join(pairs) + '}}'
svg = re.sub(r'style="([^"]*)"', style, svg)
for tag in ('path','circle','rect','line','polyline','polygon','ellipse','use','stop','image',
            'feGaussianBlur','feOffset','feMerge','feMergeNode','feFlood','feComposite','feTurbulence','feDisplacementMap'):
    svg = re.sub(rf'<{tag}\b([^>]*?)(?<!/)>', rf'<{tag}\1 />', svg)
svg = re.sub(r'\s+/>', ' />', svg)

# Fill the content width; viewBox keeps the aspect ratio.
for _ in range(2):
    svg = re.sub(r'<svg\b([^>]*?)\s(?:width|height)="[^"]*"', r'<svg\1', svg, count=1)
vb = re.search(r'viewBox="[\d.\s-]*?([\d.]+)\s+([\d.]+)"', svg)
vbw = int(float(vb.group(1))) if vb else 1000
svg = re.sub(r'<svg\b', f'<svg className="block h-auto mx-auto" style={{{{width: "100%", maxWidth: {vbw}, minWidth: {min(640, vbw)}}}}}', svg, count=1)

if not re.search(r'viewBox=', svg) or '<title' not in svg or '<desc' not in svg:
    sys.exit(f'✗ {src}: svg needs viewBox, <title> and <desc>')

comp = ''.join(w.capitalize() for w in slug.split('-'))
body = '\n'.join('      ' + l if l.strip() else '' for l in svg.splitlines())
open(out, 'w', encoding='utf-8').write(
    f'export function {comp}() {{\n  return (\n    <div className="w-full min-w-0 max-w-full overflow-x-auto">\n{body}\n    </div>\n  );\n}}\n')

left = sorted(set(re.findall(r'#[0-9a-fA-F]{6}\b|rgba?\([^)]*\)', svg)))
note = f"  (off-palette, kept as drawn — don't hand-edit: {' '.join(left)})" if left else ''
print(f"import {{ {comp} }} from '@/diagrams/{slug}';{note}")
PY
done
exit "$FAIL"
