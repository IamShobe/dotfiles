"""Chart engines: bar (+ horizontal), dumbbell, slopegraph, waterfall.

Layout grammar from diagram-design's type-bar.md (incl. dumbbell), type-line.md
(slopegraph) and type-waterfall.md, on the house 1000-wide frame (plot x 80→960,
y 40→420), recoloured to the explainer palette: coral → ACCENT, ink/muted tints
→ tint('ink'|'muted', a). Honest data: value axes include zero (bar, dumbbell,
waterfall), data coordinates round but never snap, waterfalls must reconcile.
Focal text stays ink; focus is carried by the mark (accent fill/stroke, weight).
"""
from __future__ import annotations

import math

from .core import (ACCENT, INK, MONO, MUTED, PAPER, SANS, Svg, SpecError, budget, need, snap, snap_up,
                   text_width, tint)

# ---------- shared helpers (also used by matrix.py) ----------

GRID = tint('ink', 0.08)
GRID_TOP = tint('ink', 0.06)
AXIS = tint('ink', 0.25)
CONNECTOR = tint('ink', 0.6)          # 3.25:1 on paper — load-bearing hairline (dumbbell, carries)
LEGEND_LEFT, LEGEND_RIGHT = 32, 968   # core.legend_strip defaults for a 1000-wide svg


def num(v, where: str) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise SpecError(f'{where} must be a number (got {v!r})')
    return float(v)


def fmt(v: float, signed: bool = False) -> str:
    """Print one complete number: integers bare, otherwise up to 2 decimals. Minus is U+2212."""
    r = round(v, 2)
    s = str(int(round(r))) if abs(r - round(r)) < 1e-9 else f'{r:.2f}'.rstrip('0').rstrip('.')
    s = s.lstrip('-')
    if v < 0 and s != '0':
        return '−' + s
    return ('+' + s) if signed and s != '0' else s


def nice_domain(lo: float, hi: float, zero: bool = True, max_intervals: int = 6):
    """Round axis bounds that contain [lo, hi] (and 0 when `zero`), with 4–6 even ticks.
    Follows the dumbbell honesty cases: all-zero data gets a finite 0–1 span."""
    if zero:
        lo, hi = min(lo, 0.0), max(hi, 0.0)
    if lo == hi:
        if lo == 0:
            hi = 1.0
        else:
            pad = abs(lo) * 0.1
            lo, hi = lo - pad, hi + pad
    span = hi - lo
    k0 = math.floor(math.log10(span / max_intervals)) - 1
    for k in range(k0, k0 + 4):
        for m in (1, 2, 2.5, 5):
            step = m * 10 ** k
            f = math.floor(round(lo / step, 9)) * step
            c = math.ceil(round(hi / step, 9)) * step
            if (c - f) / step <= max_intervals + 1e-9:
                n = int(round((c - f) / step))
                ticks = [round(f + i * step, 10) for i in range(n + 1)]
                return f, c, ticks
    raise SpecError('could not find round axis bounds — check the values')  # unreachable


def legend_note(svg: Svg, legend_y: float, note: str | None) -> None:
    """Right-aligned source/scale line on the legend row, or on its own row below when the
    keys leave no room. Mirrors core.legend_strip's wrapping so the two never overlap."""
    if not note:
        return
    s = note.upper()
    w = text_width(s, 8, True) + len(s) * 0.48
    if not svg.legend:
        svg.text('top', LEGEND_LEFT, legend_y + 12, s, size=8, mono=True, fill=MUTED, spacing='0.06em')
        svg.height = snap_up(legend_y + 32)
        return
    x, row_y, rows = LEGEND_LEFT + 72, legend_y + 21, 1
    for _, label in svg.legend:
        item_w = 32 + text_width(label, 11) + 28
        if x + item_w > LEGEND_RIGHT and x > LEGEND_LEFT + 72:
            x, row_y, rows = LEGEND_LEFT + 72, row_y + 20, rows + 1
        x += snap_up(item_w, 8)
    if rows == 1 and x + w + 8 <= LEGEND_RIGHT:
        svg.text('top', LEGEND_RIGHT, row_y + 4, s, size=8, mono=True, fill=MUTED, spacing='0.06em', anchor='end')
    else:
        if w > LEGEND_RIGHT - LEGEND_LEFT - 72:
            raise SpecError(f'note "{note}" is too long for one line — cut it to ~{int((LEGEND_RIGHT - LEGEND_LEFT - 72) / 5.4)} chars')
        ny = row_y + 24
        svg.text('top', LEGEND_LEFT + 72, ny, s, size=8, mono=True, fill=MUTED, spacing='0.06em')
        svg.height = max(svg.height, snap_up(ny + 24))


def axis_title_rotated(svg: Svg, s: str, cx: float = 24, cy: float = 230) -> None:
    svg.el('labels', 'text', s.upper(), x=cx, y=cy, fill=MUTED, font_size=7, font_family=MONO,
           letter_spacing='0.14em', text_anchor='middle', transform=f'rotate(-90 {cx:g} {cy:g})')


def key_line_dot(svg: Svg, color: str, width: float, r: float, label: str) -> None:
    """Legend key: a 24px line with its endpoint dot (slopegraph grammar)."""
    # {x}/{y} are substituted by core._swatch; x2 needs x+24 so draw with a path relative move.
    g = (f'glyph:<path d="M {{x}} {{y}} h 24" stroke="{color}" stroke-width="{width:g}" fill="none"/>'
         f'<circle cx="{{x}}" cy="{{y}}" r="{r:g}" fill="{color}" transform="translate(12 0)"/>')
    svg.key(g, label)


def key_ramp(svg: Svg, alphas, label: str) -> None:
    """Legend key: a 24px discrete ink ramp (5 steps), low → high left to right."""
    parts = []
    for i, a in enumerate(alphas):
        parts.append(f'<rect x="{{x}}" y="{{y}}" width="4.8" height="12" fill="{tint("ink", a)}" '
                     f'transform="translate({i * 4.8:g} -6)"/>')
    svg.key('glyph:' + ''.join(parts), label)


def check_count(what: str, n: int, lo: int, hi: int, over: str, under: str) -> None:
    if n < lo:
        raise SpecError(f'{what}: {n} < {lo} — {under}')
    budget(what, n, hi, over)


def one_focal(items, what: str) -> int | None:
    idx = [i for i, it in enumerate(items) if it.get('focal')]
    if len(idx) > 1:
        raise SpecError(f'{len(idx)} focal {what} > 1 — accent exactly one (the one the title is about); '
                        f'"everything is important" = nothing is')
    return idx[0] if idx else None


def keys(spec: dict) -> dict:
    k = spec.get('keys', {})
    if not isinstance(k, dict):
        raise SpecError('"keys" must be an object of legend labels, e.g. {"focal": "...", "rest": "..."}')
    return k


# ---------- bar ----------

def _bar_vertical(spec, bars, vals, focal, unit):
    n = len(bars)
    svg = Svg(width=1000, height=500)
    L, R, T, B = 80, 960, 40, 420
    f, c, ticks = nice_domain(min(vals), max(vals))
    y = lambda v: round(B - (v - f) / (c - f) * (B - T), 1)
    pitch = (R - L) / n
    bw = snap(max(pitch * 0.5, min(pitch * 0.66, 120)))
    for t in ticks:
        if t == f:
            continue
        svg.el('zones', 'line', x1=L, y1=y(t), x2=R, y2=y(t), stroke=GRID_TOP if t == c else GRID, stroke_width=0.8)
        svg.text('labels', 72, y(t) + 4, fmt(t), size=8, mono=True, fill=MUTED, anchor='end')
    svg.text('labels', 72, y(f) + 4, fmt(f), size=8, mono=True, fill=MUTED, anchor='end')
    svg.el('zones', 'line', x1=L, y1=T, x2=L, y2=B, stroke=AXIS, stroke_width=1)
    svg.el('zones', 'line', x1=L, y1=y(0), x2=R, y2=y(0), stroke=AXIS, stroke_width=1)
    if unit:
        axis_title_rotated(svg, unit)
    k = keys(spec)
    for i, (b, v) in enumerate(zip(bars, vals)):
        cx = L + pitch * (i + 0.5)
        x = round(cx - bw / 2, 1)
        top, bot = min(y(v), y(0)), max(y(v), y(0))
        is_f = i == focal
        fill, stroke = (tint('accent', 0.12), ACCENT) if is_f else (tint('muted', 0.15), MUTED)
        svg.el('nodes', 'rect', x=x, y=top, width=bw, height=round(bot - top, 1), fill=PAPER)
        svg.el('nodes', 'rect', x=x, y=top, width=bw, height=round(bot - top, 1), fill=fill, stroke=stroke,
               stroke_width=1.2 if is_f else 1, data_value=fmt(v), data_name=b['label'])
        svg.text('labels', cx, top - 8, fmt(v), size=8, mono=True, fill=INK if is_f else MUTED, anchor='middle',
                 weight=600 if is_f else None)
        lw = text_width(b['label'], 11, weight=600)
        if lw > pitch - 8:
            raise SpecError(f"bar label '{b['label']}' (~{lw:.0f}px) doesn't fit a {pitch:.0f}px column at {n} bars "
                            f"— shorten it (≤{int((pitch - 8) / 6.4)} chars) or set \"horizontal\": true")
        svg.text('labels', cx, 440, b['label'], size=11, weight=600, fill=INK, anchor='middle')
    if focal is not None:
        svg.key(f'swatch:{tint("accent", 0.12)}|{ACCENT}', k.get('focal') or bars[focal].get('note') or bars[focal]['label'])
        svg.key(f'swatch:{tint("muted", 0.15)}|{MUTED}', k.get('rest', 'Others'))
    ly = 468
    svg.height = ly
    return svg, ly


def _bar_horizontal(spec, bars, vals, focal, unit):
    n = len(bars)
    svg = Svg(width=1000, height=500)
    gutter = max(160, snap_up(max(text_width(b['label'], 11, weight=600) for b in bars) + 44))
    L, R, T = gutter, 920, 40
    pitch = min(48, 380 / n)
    bh = snap(pitch * 0.6)
    B = T + pitch * n
    f, c, ticks = nice_domain(min(vals), max(vals))
    x = lambda v: round(L + (v - f) / (c - f) * (R - L), 1)
    for t in ticks:
        if t != f:
            svg.el('zones', 'line', x1=x(t), y1=T, x2=x(t), y2=B, stroke=GRID, stroke_width=0.8)
        svg.text('labels', x(t), B + 16, fmt(t), size=8, mono=True, fill=MUTED, anchor='middle')
    svg.el('zones', 'line', x1=x(0), y1=T - 8, x2=x(0), y2=B, stroke=AXIS, stroke_width=1)
    if unit:
        svg.text('labels', (L + R) / 2, B + 32, unit.upper(), size=7, mono=True, fill=MUTED, anchor='middle', spacing='0.14em')
    k = keys(spec)
    for i, (b, v) in enumerate(zip(bars, vals)):
        cy = T + pitch * (i + 0.5)
        left, right = min(x(v), x(0)), max(x(v), x(0))
        is_f = i == focal
        fill, stroke = (tint('accent', 0.12), ACCENT) if is_f else (tint('muted', 0.15), MUTED)
        svg.el('nodes', 'rect', x=left, y=round(cy - bh / 2, 1), width=round(right - left, 1), height=bh, fill=PAPER)
        svg.el('nodes', 'rect', x=left, y=round(cy - bh / 2, 1), width=round(right - left, 1), height=bh, fill=fill,
               stroke=stroke, stroke_width=1.2 if is_f else 1, data_value=fmt(v), data_name=b['label'])
        svg.text('labels', right + 8, cy + 3, fmt(v), size=8, mono=True, fill=INK if is_f else MUTED, weight=600 if is_f else None)
        svg.text('labels', L - 12, cy + 4, b['label'], size=11, weight=600, fill=INK, anchor='end')
    if focal is not None:
        svg.key(f'swatch:{tint("accent", 0.12)}|{ACCENT}', k.get('focal') or bars[focal].get('note') or bars[focal]['label'])
        svg.key(f'swatch:{tint("muted", 0.15)}|{MUTED}', k.get('rest', 'Others'))
    ly = snap_up(B + (48 if unit else 36))
    svg.height = ly
    return svg, ly


def render_bar(spec: dict):
    need(spec, 'bars')
    bars = spec['bars']
    if not isinstance(bars, list):
        raise SpecError('"bars" must be a list of {"label", "value", "focal"?}')
    horizontal = bool(spec.get('horizontal'))
    if horizontal:
        check_count('bars', len(bars), 3, 12, 'group the tail into "Other" or split into two charts',
                    'a sentence says it better')
    else:
        check_count('bars', len(bars), 3, 8, 'group into periods, or set "horizontal": true (up to 12)',
                    'a sentence says it better')
    vals = []
    for i, b in enumerate(bars):
        if 'label' not in b or 'value' not in b:
            raise SpecError(f'bars[{i}] needs "label" and "value"')
        v = num(b['value'], f"bars[{i}].value ('{b['label']}')")
        if v < 0:
            raise SpecError(f"bars[{i}] '{b['label']}' is negative — bars measure magnitudes from 0; "
                            f'use a waterfall for signed changes or a dumbbell for before/after')
        vals.append(v)
    focal = one_focal(bars, 'bars')
    unit = spec.get('unit', '')
    svg, ly = (_bar_horizontal if horizontal else _bar_vertical)(spec, bars, vals, focal, unit)
    legend_note(svg, ly, spec.get('note'))
    return svg, ly


BAR_EXAMPLE = {
    "type": "bar", "slug": "bundle-by-package",
    "title": "Bundle size by package after the split",
    "desc": "Gzipped bundle size per package after the charting split; the editor package is still the largest at 212 kB.",
    "unit": "gzipped kB",
    "bars": [
        {"label": "app-shell", "value": 64},
        {"label": "editor", "value": 212, "focal": True, "note": "editor · still the heaviest"},
        {"label": "charts", "value": 138},
        {"label": "auth", "value": 22},
        {"label": "billing", "value": 47},
        {"label": "settings", "value": 31},
    ],
    "keys": {"rest": "Other packages"},
    "note": "production build, gzip -9",
}


# ---------- dumbbell ----------

_DB_ROWS = {4: (88, 96), 5: (64, 96), 6: (64, 76), 7: (52, 72), 8: (48, 68)}
_DB_ORDER = {'from': 'by {a}', 'to': 'by {b}', 'change': 'by signed change', 'abs-change': 'by absolute change'}


def render_dumbbell(spec: dict):
    need(spec, 'rows', 'series')
    rows, series = spec['rows'], spec['series']
    if not (isinstance(series, list) and len(series) == 2 and all(isinstance(s, str) and s for s in series)):
        raise SpecError('"series" must name exactly two ends, e.g. ["before", "after"] — a third dot makes it a dot plot')
    check_count('dumbbell rows', len(rows), 4, 8, 'group rows or split into two charts',
                'a sentence or a bar chart says it better')
    data = []
    for i, r in enumerate(rows):
        for kk in ('label', 'from', 'to'):
            if kk not in r:
                raise SpecError(f'rows[{i}] needs "label", "from", "to" — a missing end must be disclosed, not dropped')
        data.append((r, num(r['from'], f"rows[{i}].from ('{r['label']}')"), num(r['to'], f"rows[{i}].to ('{r['label']}')")))
    sort = spec.get('sort', 'given')
    if sort != 'given':
        if sort not in _DB_ORDER:
            raise SpecError(f'"sort" must be one of: given, {", ".join(_DB_ORDER)}')
        key = {'from': lambda d: -d[1], 'to': lambda d: -d[2], 'change': lambda d: d[2] - d[1],
               'abs-change': lambda d: -abs(d[2] - d[1])}[sort]
        data.sort(key=key)
    focal = one_focal([d[0] for d in data], 'rows')

    n = len(data)
    pitch, first = _DB_ROWS[n]
    gutter = max(200, snap_up(max(text_width(d[0]['label'], 11, weight=600) for d in data) + 44))
    L, R = gutter, 960
    svg = Svg(width=1000, height=500)
    lo = min(min(d[1], d[2]) for d in data)
    hi = max(max(d[1], d[2]) for d in data)
    f, c, ticks = nice_domain(lo, hi)
    x = lambda v: round(L + (v - f) / (c - f) * (R - L))
    for t in ticks:
        if t == f:
            svg.el('zones', 'line', x1=x(t), y1=40, x2=x(t), y2=420, stroke=AXIS, stroke_width=1)
        elif t == 0:
            svg.el('zones', 'line', x1=x(t), y1=40, x2=x(t), y2=420, stroke=AXIS, stroke_width=1)
        else:
            svg.el('zones', 'line', x1=x(t), y1=56, x2=x(t), y2=408, stroke=GRID, stroke_width=0.8)
        svg.text('labels', x(t), 440, fmt(t), size=8, mono=True, fill=MUTED, anchor='middle')
    unit = spec.get('unit', '')
    if unit:
        svg.text('labels', (L + R) / 2, 456, unit.upper(), size=7, mono=True, fill=MUTED, anchor='middle', spacing='0.14em')

    for i, (r, a, b) in enumerate(data):
        yy = first + i * pitch
        xa, xb = x(a), x(b)
        rad = 6 if abs(xa - xb) >= 16 else 4          # too close: shrink marks, never move them
        is_f = i == focal
        svg.el('edges', 'line', x1=xa, y1=yy, x2=xb, y2=yy, stroke=tint('ink', 0.85) if is_f else CONNECTOR,
               stroke_width=2 if is_f else 1, data_row=r['label'], data_from=fmt(a), data_to=fmt(b))
        svg.el('nodes', 'circle', cx=xa, cy=yy, r=rad, fill=PAPER, stroke=MUTED, stroke_width=1.5)
        svg.el('nodes', 'circle', cx=xb, cy=yy, r=rad, fill=ACCENT, stroke=INK, stroke_width=1)
        (xl, vl), (xr, vr) = sorted([(xa, a), (xb, b)])
        lab_fill, lab_w = (INK, 600) if is_f else (MUTED, None)
        wl = text_width(fmt(vl), 8, True)
        if xl - 12 - wl < L + 4:          # floor exception: would crowd the axis / row label
            svg.text('labels', xl, yy - 10, fmt(vl), size=8, mono=True, fill=lab_fill, weight=lab_w, anchor='middle')
        else:
            svg.text('labels', xl - 12, yy + 4, fmt(vl), size=8, mono=True, fill=lab_fill, weight=lab_w, anchor='end')
        wr = text_width(fmt(vr), 8, True)
        if xr + 12 + wr > 996:
            svg.text('labels', xr, yy - 10, fmt(vr), size=8, mono=True, fill=lab_fill, weight=lab_w, anchor='middle')
        else:
            svg.text('labels', xr + 12, yy + 4, fmt(vr), size=8, mono=True, fill=lab_fill, weight=lab_w)
        svg.text('labels', L - 12, yy + 4, r['label'], size=11, weight=700 if is_f else 600, fill=INK, anchor='end')

    svg.key(f'ring:{MUTED}', series[0])
    svg.key(f'glyph:<circle cx="{{x}}" cy="{{y}}" r="5" fill="{ACCENT}" stroke="{INK}" stroke-width="1" transform="translate(8 0)"/>', series[1])
    order = 'rows as listed' if sort == 'given' else 'rows ' + _DB_ORDER[sort].format(a=series[0], b=series[1])
    ly = 468
    svg.height = ly
    legend_note(svg, ly, spec.get('note') or f'{order} · axis from {fmt(f)}')
    return svg, ly


DUMBBELL_EXAMPLE = {
    "type": "dumbbell", "slug": "p95-by-endpoint",
    "title": "p95 latency per endpoint, before → after pooling",
    "desc": "p95 latency of six API endpoints before and after connection pooling; every endpoint got faster, search the most (480 to 190 ms).",
    "unit": "p95 latency, ms",
    "series": ["before", "after pooling"],
    "sort": "abs-change",
    "rows": [
        {"label": "GET /search", "from": 480, "to": 190},
        {"label": "POST /orders", "from": 360, "to": 210},
        {"label": "GET /orders/:id", "from": 220, "to": 120},
        {"label": "GET /catalog", "from": 170, "to": 110},
        {"label": "POST /login", "from": 140, "to": 118},
        {"label": "GET /health", "from": 14, "to": 9},
    ],
}


# ---------- slopegraph ----------

def _dodge(ys: list[float], gap: float, lo: float, hi: float) -> list[float]:
    """Spread label baselines ≥ gap apart, keeping order and staying near their points.
    Only labels move; the data points never do."""
    order = sorted(range(len(ys)), key=lambda i: ys[i])
    pos = [ys[i] for i in order]
    for _ in range(200):
        moved = False
        for j in range(1, len(pos)):
            d = pos[j] - pos[j - 1]
            if d < gap - 1e-6:
                push = (gap - d) / 2
                pos[j - 1] -= push
                pos[j] += push
                moved = True
        if pos and pos[0] < lo:
            sh = lo - pos[0]
            pos = [p + sh for p in pos]
        if pos and pos[-1] > hi:
            sh = pos[-1] - hi
            pos = [p - sh for p in pos]
        if not moved:
            break
    out = [0.0] * len(ys)
    for k, i in enumerate(order):
        out[i] = pos[k]
    return out


def render_slopegraph(spec: dict):
    need(spec, 'states', 'series')
    states, series = spec['states'], spec['series']
    if not (isinstance(states, list) and len(states) == 2):
        raise SpecError('"states" must be exactly two, e.g. ["v1.8", "v1.9"] — three or more states is a line or bump chart')
    check_count('slopegraph series', len(series), 4, 10, 'endpoint labels will collide — cut to the series the story needs',
                'a sentence or a pair of bars says it better')
    data = []
    for i, s in enumerate(series):
        for kk in ('name', 'from', 'to'):
            if kk not in s:
                raise SpecError(f'series[{i}] needs "name", "from", "to" — a series missing an end is dropped *and named in the note*, never interpolated')
        a = round(num(s['from'], f"series[{i}].from"), 2)
        b = round(num(s['to'], f"series[{i}].to"), 2)
        data.append((s, a, b))
    seen = {}
    for s, a, b in data:
        if (a, b) in seen:
            raise SpecError(f"'{s['name']}' and '{seen[(a, b)]}' coincide at both ends — merge them into one labelled line or drop one and say so in the note")
        seen[(a, b)] = s['name']
    focal = one_focal([d[0] for d in data], 'series')

    svg = Svg(width=1000, height=500)
    XA, XB, T, B = 320, 680, 40, 420
    for s, _, _ in data:
        if text_width(s['name'], 11, weight=600) > 232:
            raise SpecError(f"series name '{s['name']}' is too long for the 232px label gutter — shorten it (≤36 chars)")
    lo = min(min(a, b) for _, a, b in data)
    hi = max(max(a, b) for _, a, b in data)
    f, c, _ = nice_domain(lo, hi, zero=bool(spec.get('zero', False)))
    y = lambda v: round(B - (v - f) / (c - f) * (B - T), 1)
    unit = spec.get('unit', '')
    if unit:
        axis_title_rotated(svg, unit)
    for ax, xx, st in (('from', XA, states[0]), ('to', XB, states[1])):
        svg.el('zones', 'line', x1=xx, y1=T, x2=xx, y2=B, stroke=AXIS, stroke_width=1)
        svg.el('labels', 'text', str(st).upper(), data_axis=ax, data_state=str(st).upper(), x=xx, y=440, fill=MUTED,
               font_size=9, font_family=MONO, letter_spacing='0.14em', text_anchor='middle')

    # ink ramp 0.86 → 0.66 ordered by the left-hand value (strongest = highest before); floor 0.58 ≈ 3:1
    rest = sorted([i for i in range(len(data)) if i != focal], key=lambda i: -data[i][1])
    ramp = {}
    for k, i in enumerate(rest):
        ramp[i] = 0.86 - (0.20 * k / (len(rest) - 1) if len(rest) > 1 else 0)
    ly_from = _dodge([y(a) + 3.5 for _, a, _ in data], 12, T + 4, B + 4)
    ly_to = _dodge([y(b) + 3.5 for _, _, b in data], 12, T + 4, B + 4)

    for i, (s, a, b) in enumerate(data):
        is_f = i == focal
        col = ACCENT if is_f else tint('ink', round(ramp[i], 2))
        layer = 'top' if is_f else 'nodes'
        svg.el('edges' if not is_f else 'labels_under', 'line', data_series=s['name'], data_from=fmt(a), data_to=fmt(b),
               x1=XA, y1=y(a), x2=XB, y2=y(b), stroke=col, stroke_width=2.4 if is_f else 1.2)
        rr = 4 if is_f else 3
        svg.el(layer, 'circle', cx=XA, cy=y(a), r=rr, fill=col)
        svg.el(layer, 'circle', cx=XB, cy=y(b), r=rr, fill=col)
        wgt = 600 if is_f else 500
        for end, xx, anchor, txt, yy, role in (
                ('from', 272, 'end', s['name'], ly_from[i], 'name'), ('from', 304, 'end', fmt(a), ly_from[i], None),
                ('to', 696, None, fmt(b), ly_to[i], None), ('to', 728, None, s['name'], ly_to[i], 'name')):
            is_name = role == 'name'
            svg.el('labels', 'text', txt, data_series=s['name'], data_end=end, data_role=role, x=xx, y=round(yy, 1),
                   fill=INK if is_name else MUTED, font_size=11 if is_name else 9,
                   font_weight=wgt if is_name else None, font_family=SANS if is_name else MONO,
                   text_anchor=anchor)
    k = keys(spec)
    if focal is not None:
        key_line_dot(svg, ACCENT, 2.4, 4, k.get('focal') or data[focal][0].get('note') or f"{data[focal][0]['name']} · focal")
    key_line_dot(svg, tint('ink', 0.86), 1.2, 3, k.get('rest', f'Others · strongest tone was highest at {states[0]}'))
    ly = 468
    svg.height = ly
    unit_s = f' {unit}' if unit and len(unit) <= 4 else ''
    legend_note(svg, ly, spec.get('note') or f'same {fmt(f)}–{fmt(c)}{unit_s} scale on both axes')
    return svg, ly


SLOPEGRAPH_EXAMPLE = {
    "type": "slopegraph", "slug": "p95-by-service-release",
    "title": "One service went the other way in v1.9",
    "desc": "p95 latency per service in releases v1.8 and v1.9 on one shared scale; four services got faster after the cache rollout, recommendations got slower.",
    "unit": "p95 latency, ms",
    "states": ["v1.8", "v1.9"],
    "series": [
        {"name": "search", "from": 512, "to": 208},
        {"name": "catalog", "from": 376, "to": 164},
        {"name": "checkout", "from": 291, "to": 143},
        {"name": "auth", "from": 154, "to": 121},
        {"name": "recommendations", "from": 238, "to": 431, "focal": True, "note": "recommendations · the only regression"},
    ],
}


# ---------- waterfall ----------

def render_waterfall(spec: dict):
    need(spec, 'steps')
    steps = spec['steps']
    check_count('waterfall bars', len(steps), 3, 8, 'merge the smallest bridges into one named "Other" step (say what it holds) or split the walk',
                'show the two totals as a sentence')
    for i, s in enumerate(steps):
        if 'label' not in s or 'value' not in s or s.get('role') not in ('total', 'delta', 'subtotal'):
            raise SpecError(f'steps[{i}] needs "label", "value" and "role": total | delta | subtotal')
    if steps[0]['role'] != 'total' or steps[-1]['role'] != 'total':
        raise SpecError('a waterfall starts and ends on a "total" step — first and last steps must have role "total"')
    if any(s['role'] == 'total' for s in steps[1:-1]):
        raise SpecError('only the first and last steps are "total" — a resting point mid-walk is a "subtotal"')
    if sum(s['role'] == 'subtotal' for s in steps) > 1:
        raise SpecError('more than one subtotal — a walk that needs several resting points is two walks; split it')
    start = num(steps[0]['value'], f"steps[0].value ('{steps[0]['label']}')")
    if start <= 0:
        raise SpecError(f"start total '{steps[0]['label']}' is {fmt(start)} — a waterfall needs a positive start anchor")
    run, levels, expr = start, [], fmt(start)
    for i, s in enumerate(steps):
        v = num(s['value'], f"steps[{i}].value ('{s['label']}')")
        if i == 0:
            levels.append((0.0, start))
            continue
        if s['role'] == 'delta':
            if v == 0:
                raise SpecError(f"step '{s['label']}' is 0 — zero bridges are dropped, not drawn; mention it in the note")
            levels.append((run, run + v))
            run += v
            expr += f' {"+" if v > 0 else "−"} {fmt(abs(v))}'
        else:
            if abs(v - run) > 1e-6 * max(1.0, abs(run)):
                raise SpecError(f"{s['role']} '{s['label']}' is {fmt(v)} but {expr} = {fmt(run)} — the walk doesn't "
                                f'conserve; fix a value (a waterfall that does not add up is wrong, not approximate)')
            levels.append((0.0, v))
    focal = one_focal(steps, 'steps')
    if focal is not None and steps[focal]['role'] != 'delta':
        raise SpecError(f"focal step '{steps[focal]['label']}' is a {steps[focal]['role']} — the focal mark is the one bridge the chart exists to show")

    n = len(steps)
    svg = Svg(width=1000, height=500)
    L, R, T, B = 80, 960, 40, 420
    all_levels = [v for lv in levels for v in lv]
    f, c, ticks = nice_domain(min(all_levels), max(all_levels))
    y = lambda v: round(B - (v - f) / (c - f) * (B - T), 1)
    for t in ticks:
        if t != f and t != 0:
            svg.el('zones', 'line', x1=L, y1=y(t), x2=R, y2=y(t), stroke=GRID_TOP if t == c else GRID, stroke_width=0.8)
        svg.text('labels', 72, y(t) + 4, fmt(t), size=8, mono=True, fill=MUTED, anchor='end')
    svg.el('zones', 'line', x1=L, y1=T, x2=L, y2=B, stroke=AXIS, stroke_width=1)
    svg.el('zones', 'line', x1=L, y1=y(0), x2=R, y2=y(0), stroke=AXIS, stroke_width=1)
    unit = spec.get('unit', '')
    if unit:
        axis_title_rotated(svg, unit)
    pitch = (R - L) / n
    bw = snap(max(pitch * 0.5, min(pitch * 0.66, 120)))
    k = keys(spec)
    used = set()
    prev_right, prev_level = None, None
    for i, (s, (a, b)) in enumerate(zip(steps, levels)):
        cx = L + pitch * (i + 0.5)
        x = round(cx - bw / 2, 1)
        top, bot = min(y(a), y(b)), max(y(a), y(b))
        role = s['role']
        v = b - a if role == 'delta' else b
        if role != 'delta':
            fill, stroke, kind = tint('ink', 0.08), INK, 'total'
        elif i == focal:
            fill, stroke, kind = tint('accent', 0.12), ACCENT, 'focal'
        elif v > 0:
            fill, stroke, kind = tint('muted', 0.15), MUTED, 'inc'
        else:
            fill, stroke, kind = PAPER, MUTED, 'dec'
        used.add(kind)
        if prev_right is not None:
            svg.el('edges', 'line', x1=prev_right, y1=y(prev_level), x2=x, y2=y(prev_level), stroke=CONNECTOR,
                   stroke_width=1, data_carry=fmt(prev_level))
        svg.el('nodes', 'rect', x=x, y=top, width=bw, height=round(bot - top, 1), fill=PAPER)
        svg.el('nodes', 'rect', x=x, y=top, width=bw, height=round(bot - top, 1), fill=fill, stroke=stroke,
               stroke_width=1.2 if kind == 'focal' else 1, data_role=role,
               data_value=fmt(v, signed=role == 'delta').replace('−', '-'), data_name=s['label'])
        txt = fmt(v, signed=role == 'delta')
        is_f = kind == 'focal'
        if role == 'delta' and v < 0 and bot + 12 <= 428:
            ty = bot + 12
        else:
            ty = top - 8
        svg.text('labels', cx, ty, txt, size=8, mono=True, fill=INK if is_f else MUTED, anchor='middle', weight=600 if is_f else None)
        lw = text_width(s['label'], 11, weight=600)
        if lw > pitch - 8:
            raise SpecError(f"step label '{s['label']}' (~{lw:.0f}px) doesn't fit a {pitch:.0f}px column at {n} steps — shorten it (≤{int((pitch - 8) / 6.4)} chars)")
        svg.text('labels', cx, 440, s['label'], size=11, weight=600, fill=INK, anchor='middle')
        prev_right, prev_level = round(x + bw, 1), b
    has_sub = any(s['role'] == 'subtotal' for s in steps)
    svg.key(f'swatch:{tint("ink", 0.08)}|{INK}', k.get('total', 'Start / subtotal / end' if has_sub else 'Start / end total'))
    if 'inc' in used:
        svg.key(f'swatch:{tint("muted", 0.15)}|{MUTED}', k.get('increase', 'Increase'))
    if 'dec' in used:
        svg.key(f'swatch:{PAPER}|{MUTED}', k.get('decrease', 'Decrease'))
    if 'focal' in used:
        svg.key(f'swatch:{tint("accent", 0.12)}|{ACCENT}', k.get('focal') or steps[focal].get('note') or steps[focal]['label'])
    ly = 468
    svg.height = ly
    legend_note(svg, ly, spec.get('note') or f'{expr} = {fmt(run)}')
    return svg, ly


WATERFALL_EXAMPLE = {
    "type": "waterfall", "slug": "latency-budget",
    "title": "Where the 170 ms went",
    "desc": "Checkout p95 latency bridge from 450 ms to 280 ms: the response cache removed 120 ms, request batching 80 ms, and the new auth hop added 30 ms back.",
    "unit": "p95 latency, ms",
    "steps": [
        {"label": "before", "role": "total", "value": 450},
        {"label": "cache", "role": "delta", "value": -120, "focal": True, "note": "response cache · biggest saving"},
        {"label": "batching", "role": "delta", "value": -80},
        {"label": "auth hop", "role": "delta", "value": 30},
        {"label": "after", "role": "total", "value": 280},
    ],
    "keys": {"total": "Before / after", "increase": "Latency added", "decrease": "Latency removed"},
}


TYPES = {
    'bar': (render_bar, BAR_EXAMPLE, 'one value per category (4–8, or 12 horizontal), one focal bar; axis from 0'),
    'dumbbell': (render_dumbbell, DUMBBELL_EXAMPLE, 'two values per row (before/after) where the gap is the message; 4–8 rows'),
    'slopegraph': (render_slopegraph, SLOPEGRAPH_EXAMPLE, 'several series across exactly two states: direction, steepness, crossings'),
    'waterfall': (render_waterfall, WATERFALL_EXAMPLE, 'start total → signed contributions → end total that must reconcile'),
}
