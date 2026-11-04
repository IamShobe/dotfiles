"""Shared primitives for the explainer diagram renderer.

Every engine builds an `Svg`, draws with the helpers below, and returns it; the
entry point (render.py) wraps it with the accessible root, markers and legend.
Visual rules come from references/diagram-brief.md (diagram-design v2.6 with the
explainer palette): 4px grid, orthogonal r=8 connectors, masked labels 6-10px
off their line, focal accent on at most two elements, legend strip at the bottom.
Output is light-theme hexes only; diagram-to-jsx.sh maps them to theme vars.
"""
from __future__ import annotations

import math
import unicodedata
from dataclasses import dataclass, field
from html import escape

# ---------- palette (explainer profile, light) ----------

PAPER = '#ffffff'
PAPER_2 = '#fafbfb'
INK = '#414448'
MUTED = '#62676c'
SOFT = '#6f767d'
RULE = '#e3e6e8'
RULE_SOLID = '#d1d5d9'
ACCENT = '#4f46e5'
LINK = '#4338ca'
SIGNAL = '#ffc533'
ADD = '#1a7f52'
RM = '#c2415a'

_RGB = {'ink': (65, 68, 72), 'muted': (98, 103, 108), 'soft': (111, 118, 125), 'accent': (79, 70, 229)}


def tint(role: str, a: float) -> str:
    """rgba() of a palette role at alpha `a`; the converter maps these to color-mix(var)."""
    r, g, b = _RGB[role]
    return f'rgba({r},{g},{b},{a:g})'


SANS = "'Geist', ui-sans-serif, system-ui, sans-serif"
MONO = "'Geist Mono', ui-monospace, monospace"


class SpecError(Exception):
    """A spec problem the author must fix (bad field, over budget). Message says how."""


# ---------- geometry helpers ----------

def snap(v: float, g: int = 4) -> int:
    return int(round(v / g) * g)


def snap_up(v: float, g: int = 4) -> int:
    return int(math.ceil(v / g) * g)


def text_width(s: str, size: float, mono: bool = False, weight: int = 400) -> float:
    """Estimated rendered width. Wide/full-width chars cost 1em; marks cost 0."""
    adv = 0.62 if mono else (0.61 if weight >= 600 else 0.58)
    w = 0.0
    for ch in str(s):
        if unicodedata.combining(ch):
            continue
        w += size if unicodedata.east_asian_width(ch) in ('W', 'F') else size * adv
    return w


NODE_WIDTHS = (80, 96, 112, 120, 128, 144, 160, 176, 192, 200, 240, 280, 320)   # halves stay on the 4px grid


def fit_width(*texts_and_sizes, pad: int = 16, minimum: int = 96) -> int:
    """Smallest allowed node width that fits every (text, size, mono, weight) with padding."""
    need = minimum
    for t in texts_and_sizes:
        if t and t[0]:
            text, size, mono, weight = (list(t) + [False, 400])[:4]
            need = max(need, text_width(text, size, mono, weight) + 2 * pad)
    for w in NODE_WIDTHS:
        if w >= need:
            return w
    return snap_up(need, 8)


# ---------- svg builder ----------

def _attrs(d: dict) -> str:
    out = []
    for k, v in d.items():
        if v is None or v is False:
            continue
        k = k.rstrip('_').replace('_', '-')
        out.append(f'{k}="{escape(str(v), quote=True)}"' if v is not True else k)
    return (' ' + ' '.join(out)) if out else ''


@dataclass
class Svg:
    """Collects layers in paint order. Draw into the layer that matches z-order:
    'zones' < 'edges' < 'labels_under' < 'nodes' < 'labels' < 'top'."""
    width: int = 1000
    height: int = 600
    layers: dict = field(default_factory=lambda: {k: [] for k in ('zones', 'edges', 'labels_under', 'nodes', 'labels', 'top')})
    markers: set = field(default_factory=set)
    defs_extra: list = field(default_factory=list)
    legend: list = field(default_factory=list)   # (swatch_kind, label) in first-seen order

    def el(self, layer: str, tag: str, text: str | None = None, **a) -> None:
        body = '' if text is None else escape(str(text), quote=False)
        self.layers[layer].append(f'<{tag}{_attrs(a)}>{body}</{tag}>' if text is not None else f'<{tag}{_attrs(a)}/>')

    def raw(self, layer: str, s: str) -> None:
        self.layers[layer].append(s)

    def key(self, kind: str, label: str) -> None:
        """Register a legend entry once. kind: node:<treatment> | line:<style> | dot:<color> | swatch:<fill>|<stroke>."""
        if (kind, label) not in self.legend:
            self.legend.append((kind, label))

    # --- primitives ---

    def text(self, layer, x, y, s, size=12, mono=False, weight=None, fill=INK, anchor='start', spacing=None, italic=False, upper=False):
        self.el(layer, 'text', s.upper() if upper else s, x=_n(x), y=_n(y), fill=fill, font_size=size,
                font_family=MONO if mono else SANS, font_weight=weight, text_anchor=None if anchor == 'start' else anchor,
                letter_spacing=spacing, font_style='italic' if italic else None)

    def label(self, x, y, s, anchor='middle', fill=SOFT, size=8, mono=True, upper=True, spacing='0.06em', layer='labels'):
        """Masked label: opaque paper rect behind the text. (x, y) is the text baseline."""
        s = s.upper() if upper else s
        em = float(spacing[:-2]) if spacing and spacing.endswith('em') else 0.0
        w = snap_up(text_width(s, size, mono) + len(s) * size * em + 8)
        h = size + 4
        left = snap(x - w / 2) if anchor == 'middle' else (x - 4 if anchor == 'start' else x - w + 4)
        self.el(layer, 'rect', x=_n(left), y=_n(y - size), width=w, height=h, rx=2, fill=PAPER)
        self.text(layer, x, y, s, size=size, mono=mono, fill=fill, anchor=anchor, spacing=spacing)
        return left, y - size, w, h

    def marker(self, name: str) -> str:
        self.markers.add(name)
        return f'url(#{name})'


def _n(v) -> str:
    """Compact number formatting."""
    if isinstance(v, float):
        return f'{v:.1f}'.rstrip('0').rstrip('.')
    return str(v)


# ---------- markers ----------

MARKERS = {
    'arrow': f'<marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{MUTED}"/></marker>',
    'arrow-accent': f'<marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{ACCENT}"/></marker>',
    'arrow-link': f'<marker id="arrow-link" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{LINK}"/></marker>',
    'arrow-open': f'<marker id="arrow-open" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polyline points="0 0, 8 3, 0 6" fill="none" stroke="{MUTED}" stroke-width="1.2"/></marker>',
    'arrow-sm': f'<marker id="arrow-sm" markerWidth="6" markerHeight="5" refX="5" refY="2.5" orient="auto"><polygon points="0 0, 6 2.5, 0 5" fill="{MUTED}"/></marker>',
    # UML ends (drawn at the target end, so the marker points into the target)
    'tri-hollow': f'<marker id="tri-hollow" markerWidth="14" markerHeight="12" refX="13" refY="6" orient="auto"><polygon points="1 1, 13 6, 1 11" fill="{PAPER}" stroke="{INK}" stroke-width="1"/></marker>',
    'dia-filled': f'<marker id="dia-filled" markerWidth="16" markerHeight="10" refX="15" refY="5" orient="auto"><polygon points="1 5, 8 1, 15 5, 8 9" fill="{INK}"/></marker>',
    'dia-hollow': f'<marker id="dia-hollow" markerWidth="16" markerHeight="10" refX="15" refY="5" orient="auto"><polygon points="1 5, 8 1, 15 5, 8 9" fill="{PAPER}" stroke="{INK}" stroke-width="1"/></marker>',
    'open-ink': f'<marker id="open-ink" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><polyline points="1 1, 9 4, 1 7" fill="none" stroke="{INK}" stroke-width="1.2"/></marker>',
}

# Edge styles shared by every engine: stroke, width, dash, marker.
EDGE_STYLES = {
    'default': (MUTED, 1.2, None, 'arrow'),
    'accent': (ACCENT, 1.4, None, 'arrow-accent'),
    'link': (LINK, 1.2, None, 'arrow-link'),
    'dashed': (MUTED, 1.2, '5,4', 'arrow'),        # optional / return / async / passive
    'async': (MUTED, 1.2, '5,4', 'arrow-open'),
    'transit': (MUTED, 1.0, '4,3', 'arrow'),       # rule 5 exception: passes behind a box
    'plain': (MUTED, 1.0, None, None),             # no arrowhead
}
EDGE_LEGEND = {'default': 'Flow', 'accent': 'Primary path', 'link': 'API / external call',
               'dashed': 'Optional / return', 'async': 'Async', 'transit': 'Passes through'}


def ortho_path(points: list[tuple[float, float]], r: float = 8) -> str:
    """Orthogonal polyline with quarter-arc (quadratic) bends of radius r.
    Consecutive points must share x or y. Bends shrink r if a segment is short."""
    pts = [points[0]]
    for p in points[1:]:
        if p != pts[-1]:
            pts.append(p)
    if len(pts) < 2:
        return ''
    d = [f'M {_n(pts[0][0])} {_n(pts[0][1])}']
    for i in range(1, len(pts) - 1):
        (x0, y0), (x1, y1), (x2, y2) = pts[i - 1], pts[i], pts[i + 1]
        la = math.hypot(x1 - x0, y1 - y0)
        lb = math.hypot(x2 - x1, y2 - y1)
        rr = min(r, la / 2, lb / 2)
        if rr <= 0 or (x0 == x1 == x2) or (y0 == y1 == y2):
            d.append(f'L {_n(x1)} {_n(y1)}')
            continue
        ax = x1 - math.copysign(rr, x1 - x0) if x1 != x0 else x1
        ay = y1 - math.copysign(rr, y1 - y0) if y1 != y0 else y1
        bx = x1 + math.copysign(rr, x2 - x1) if x2 != x1 else x1
        by = y1 + math.copysign(rr, y2 - y1) if y2 != y1 else y1
        d.append(f'L {_n(ax)} {_n(ay)} Q {_n(x1)} {_n(y1)} {_n(bx)} {_n(by)}')
    d.append(f'L {_n(pts[-1][0])} {_n(pts[-1][1])}')
    return ' '.join(d)


def draw_edge(svg: Svg, points, style: str = 'default', label: str | None = None, label_at: tuple | None = None,
              label_side: str = 'above', layer: str = 'edges', legend: bool = True) -> None:
    """Draw an orthogonal connector and its masked label.
    label_at = (x, y) of the segment point to label; defaults to the longest segment's midpoint.
    label_side: 'above' a horizontal segment, 'right'/'left' of a vertical one."""
    stroke, width, dash, mk = EDGE_STYLES[style]
    svg.el(layer, 'path', d=ortho_path(points), fill='none', stroke=stroke, stroke_width=width,
           stroke_dasharray=dash, marker_end=svg.marker(mk) if mk else None)
    if legend and style in EDGE_LEGEND:
        svg.key(f'line:{style}', EDGE_LEGEND[style])
    if label:
        if label_at is None:
            segs = list(zip(points, points[1:]))
            (a, b) = max(segs, key=lambda s: abs(s[1][0] - s[0][0]) + abs(s[1][1] - s[0][1]))
            label_at = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            vertical = a[0] == b[0]
            label_side = ('right' if vertical else 'above') if label_side == 'above' else label_side
        x, y = label_at
        if label_side == 'above':
            svg.label(x, y - 10, label)                 # 8px text + mask ends 6px above the line
        elif label_side == 'below':
            svg.label(x, y + 18, label)
        elif label_side == 'right':
            svg.label(x + 10, y + 3, label, anchor='start')
        else:
            svg.label(x - 10, y + 3, label, anchor='end')


# ---------- nodes ----------

# treatment → (fill, stroke, dash, legend label)
NODE_KINDS = {
    'default': (PAPER, INK, None, 'Component'),
    'focal': (tint('accent', 0.08), ACCENT, None, 'Focal / changed'),
    'store': (tint('ink', 0.05), MUTED, None, 'Store / state'),
    'external': (tint('ink', 0.03), tint('ink', 0.3), None, 'External'),
    'input': (tint('muted', 0.10), SOFT, None, 'User / input'),
    'optional': (tint('ink', 0.02), tint('ink', 0.2), '4,3', 'Optional / async'),
    'boundary': (tint('accent', 0.05), tint('accent', 0.5), '4,4', 'Boundary'),
    'new': (tint('accent', 0.08), ACCENT, None, 'New'),
    'removed': (tint('ink', 0.02), tint('ink', 0.3), '4,3', 'Removed'),
}


def node_box(svg: Svg, x, y, w, h, name: str, sub: str | None = None, tag: str | None = None,
             kind: str = 'default', rx: int = 6, legend: bool = True, name_size: int = 12) -> None:
    """Node box per the brief: opaque mask, styled box, optional type tag, name, sublabel."""
    if kind not in NODE_KINDS:
        raise SpecError(f"node kind '{kind}' unknown — use one of: {', '.join(NODE_KINDS)}")
    fill, stroke, dash, lg = NODE_KINDS[kind]
    svg.el('nodes', 'rect', x=_n(x), y=_n(y), width=_n(w), height=_n(h), rx=rx, fill=PAPER)
    svg.el('nodes', 'rect', x=_n(x), y=_n(y), width=_n(w), height=_n(h), rx=rx, fill=fill, stroke=stroke,
           stroke_width=1.2 if kind in ('focal', 'new') else 1, stroke_dasharray=dash)
    if legend:
        svg.key(f'node:{kind}', lg)
    cx = x + w / 2
    if tag:
        tw = snap_up(text_width(tag.upper(), 7, True) + 10)
        svg.el('nodes', 'rect', x=_n(x + 8), y=_n(y + 6), width=tw, height=12, rx=2, fill='none', stroke=stroke,
               stroke_opacity=0.4, stroke_width=0.8)
        svg.text('nodes', x + 8 + tw / 2, y + 15, tag.upper(), size=7, mono=True, fill=stroke, anchor='middle', spacing='0.08em')
    top = y + (8 if tag else 0)
    if sub:
        cy = top + (h - (8 if tag else 0)) / 2
        svg.text('nodes', cx, cy + 1, name, size=name_size, weight=600, anchor='middle')
        svg.text('nodes', cx, cy + 15, sub, size=9, mono=True, fill=MUTED, anchor='middle')
    else:
        svg.text('nodes', cx, top + (h - (8 if tag else 0)) / 2 + 4, name, size=name_size, weight=600, anchor='middle')


def zone(svg: Svg, x, y, w, h, label: str, dashed: bool = False) -> None:
    """Grouping container: drawn first, label on a paper mask over the top border."""
    svg.el('zones', 'rect', x=_n(x), y=_n(y), width=_n(w), height=_n(h), rx=8, fill=tint('ink', 0.02),
           stroke=tint('ink', 0.2 if dashed else 0.1), stroke_width=0.8, stroke_dasharray='4,4' if dashed else None)
    s = label.upper()
    lw = snap_up(text_width(s, 8, True) + 12)
    svg.el('zones', 'rect', x=_n(x + 12), y=_n(y - 6), width=lw, height=12, fill=PAPER)
    svg.text('zones', x + 18, y + 3, s, size=8, mono=True, fill=tint('ink', 0.55), spacing='0.14em')


# ---------- legend + document ----------

def _swatch(kind: str, x: float, y: float) -> str:
    """Legend key glyph, 24px wide, vertically centred on y."""
    cat, _, arg = kind.partition(':')
    if cat == 'node':
        fill, stroke, dash, _ = NODE_KINDS[arg]
        da = f' stroke-dasharray="{dash}"' if dash else ''
        return f'<rect x="{_n(x)}" y="{_n(y - 6)}" width="20" height="12" rx="3" fill="{fill}" stroke="{stroke}" stroke-width="1"{da}/>'
    if cat == 'line':
        stroke, width, dash, mk = EDGE_STYLES[arg]
        m = f' marker-end="url(#{mk})"' if mk else ''
        da = f' stroke-dasharray="{dash}"' if dash else ''
        return f'<line x1="{_n(x)}" y1="{_n(y)}" x2="{_n(x + 22)}" y2="{_n(y)}" stroke="{stroke}" stroke-width="{width}"{da}{m}/>'
    if cat == 'dot':
        return f'<circle cx="{_n(x + 8)}" cy="{_n(y)}" r="5" fill="{arg}"/>'
    if cat == 'ring':
        return f'<circle cx="{_n(x + 8)}" cy="{_n(y)}" r="5" fill="{PAPER}" stroke="{arg}" stroke-width="1.5"/>'
    if cat == 'swatch':
        fill, _, stroke = arg.partition('|')
        return f'<rect x="{_n(x)}" y="{_n(y - 6)}" width="20" height="12" rx="2" fill="{fill}" stroke="{stroke or "none"}" stroke-width="1"/>'
    if cat == 'glyph':   # raw svg snippet with {x},{y} placeholders
        return arg.replace('{x}', _n(x)).replace('{y}', _n(y))
    raise SpecError(f'unknown legend kind {kind}')


def legend_strip(svg: Svg, y: float, left: float = 32, right: float | None = None) -> float:
    """Horizontal legend strip under a hairline, wrapping rows. Returns the bottom y."""
    if not svg.legend:
        return y
    right = right or svg.width - 32
    svg.el('top', 'line', x1=_n(left), y1=_n(y), x2=_n(right), y2=_n(y), stroke=RULE, stroke_width=0.8)
    svg.text('top', left, y + 24, 'LEGEND', size=8, mono=True, fill=MUTED, spacing='0.14em')
    x, row_y = left + 72, y + 20
    for kind, label in svg.legend:
        for mk in ('arrow', 'arrow-accent', 'arrow-link', 'arrow-open', 'arrow-sm'):
            if f'url(#{mk})' in _swatch(kind, 0, 0):
                svg.markers.add(mk)
        item_w = 32 + text_width(label, 11) + 28
        if x + item_w > right and x > left + 72:
            x, row_y = left + 72, row_y + 20
        svg.raw('top', _swatch(kind, x, row_y))
        svg.text('top', x + 28, row_y + 4, label, size=11, fill=MUTED)
        x += snap_up(item_w, 8)
    return row_y + 16


def document(svg: Svg, slug: str, title: str, desc: str, legend_y: float | None = None) -> str:
    """Accessible bare <svg>: title first, slug-prefixed ids, markers, paper background, legend."""
    if not title or not desc:
        raise SpecError('every diagram needs "title" (≤60 chars) and "desc" (one sentence on what it shows)')
    if legend_y is not None:                     # the legend is the last thing on the page
        bottom = legend_strip(svg, legend_y) if svg.legend else legend_y - 16
        svg.height = snap_up(bottom + 24)
    defs = ''.join(MARKERS[m] for m in sorted(svg.markers)) + ''.join(svg.defs_extra)
    body = ''.join(''.join(svg.layers[k]) for k in ('zones', 'edges', 'labels_under', 'nodes', 'labels', 'top'))
    return (f'<svg viewBox="0 0 {svg.width} {svg.height}" xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-labelledby="{slug}-title {slug}-desc">'
            f'<title id="{slug}-title">{escape(title)}</title><desc id="{slug}-desc">{escape(desc)}</desc>'
            f'<defs>{defs}</defs><rect width="100%" height="100%" fill="{PAPER}"/>{body}</svg>\n')


def need(spec: dict, *keys: str) -> None:
    missing = [k for k in keys if k not in spec]
    if missing:
        raise SpecError(f"{spec.get('type')} spec is missing: {', '.join(missing)}")


def budget(what: str, n: int, limit: int, hint: str = 'split into an overview + a detail diagram, or cut') -> None:
    if n > limit:
        raise SpecError(f'{what}: {n} > {limit} (diagram-design budget) — {hint}')
