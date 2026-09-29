"""Matrix engines: quadrant (standard 2×2 with positioned items) and heatmap.

Grammar from diagram-design's type-quadrant.md and type-heatmap.md, recoloured to
the explainer palette. Quadrant: one word per axis tip, dots r=4 (focal r=6 in
accent), labels placed off-axis without collisions or the spec fails. Heatmap:
one ink ramp for every non-focal cell (monotone in value), the single focal cell
in accent and excluded from the ramp scale, complete rows × cols grid.
"""
from __future__ import annotations

import math

from .charts import AXIS, fmt, key_ramp, keys, legend_note, num, one_focal
from .core import ACCENT, INK, MONO, MUTED, PAPER, SANS, Svg, SpecError, budget, need, snap_up, text_width, tint

# ---------- quadrant ----------

_Q = dict(X0=140, X1=860, Y0=64, Y1=404)      # plot box; the axis cross sits at its centre
_ITEM = dict(x0=172, x1=828, y0=92, y1=376)    # where 0..1 item positions map (inset from the corner tags)


def _overlap(a, b, pad=2):
    return not (a[2] + pad <= b[0] or b[2] + pad <= a[0] or a[3] + pad <= b[1] or b[3] + pad <= a[1])


def _word(v, where):
    if not isinstance(v, str) or not v.strip():
        raise SpecError(f'{where} must be a word')
    if len(v.split()) != 1 or any(g in v for g in '↑↓←→()'):
        raise SpecError(f"{where} '{v}' must be ONE word, no arrows or HIGH/LOW modifiers — "
                        f"the word at the tip is the label (e.g. \"cheap\" / \"costly\")")
    return v.upper()


def render_quadrant(spec: dict):
    need(spec, 'axes', 'items')
    ax, items = spec['axes'], spec['items']
    if not (isinstance(ax, dict) and all(isinstance(ax.get(k), list) and len(ax[k]) == 2 for k in ('x', 'y'))):
        raise SpecError('"axes" must be {"x": [low word, high word], "y": [low word, high word]}')
    xw = [_word(w, f'axes.x[{i}]') for i, w in enumerate(ax['x'])]
    yw = [_word(w, f'axes.y[{i}]') for i, w in enumerate(ax['y'])]
    if not isinstance(items, list) or len(items) < 3:
        raise SpecError('quadrant needs ≥3 items — fewer is a sentence')
    budget('quadrant items', len(items), 12, 'cluster related items or split into two quadrants')
    focal = one_focal(items, 'items')

    X0, X1, Y0, Y1 = _Q['X0'], _Q['X1'], _Q['Y0'], _Q['Y1']
    cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2
    svg = Svg(width=1000, height=500)
    obstacles = []   # (x0, y0, x1, y1) boxes nothing may overlap

    # axis cross, single-ended arrows toward "high"
    svg.el('edges', 'line', x1=X0 - 20, y1=cy, x2=X1 + 20, y2=cy, stroke=tint('ink', 0.45), stroke_width=1,
           marker_end=svg.marker('arrow'))
    svg.el('edges', 'line', x1=cx, y1=Y1 + 20, x2=cx, y2=Y0 - 12, stroke=tint('ink', 0.45), stroke_width=1,
           marker_end=svg.marker('arrow'))

    def word(x, y, s, anchor):
        w = text_width(s, 9, True) + len(s) * 9 * 0.18
        svg.text('labels', x, y, s, size=9, mono=True, fill=INK, anchor=anchor, spacing='0.18em')
        l = x - w / 2 if anchor == 'middle' else (x - w if anchor == 'end' else x)
        obstacles.append((l, y - 9, l + w, y + 2))
    word(X0 - 32, cy + 3, xw[0], 'end')
    word(X1 + 32, cy + 3, xw[1], 'start')
    word(cx, Y0 - 24, yw[1], 'middle')
    word(cx, Y1 + 40, yw[0], 'middle')
    for w in xw[:1]:
        if text_width(w, 9, True) + len(w) * 1.62 > X0 - 32 - 24:
            raise SpecError(f"axis word '{w}' is too long for the left margin — use ≤10 letters")
    if text_width(xw[1], 9, True) + len(xw[1]) * 1.62 > 1000 - (X1 + 32) - 16:
        raise SpecError(f"axis word '{xw[1]}' is too long for the right margin — use ≤10 letters")

    # item geometry
    pts = []
    for i, it in enumerate(items):
        if 'label' not in it or 'x' not in it or 'y' not in it:
            raise SpecError(f'items[{i}] needs "label", "x" (0..1) and "y" (0..1)')
        x, y = num(it['x'], f'items[{i}].x'), num(it['y'], f'items[{i}].y')
        if not (0 <= x <= 1 and 0 <= y <= 1):
            raise SpecError(f"items[{i}] '{it['label']}' is off the grid — x and y run 0..1 (0.5 is the axis)")
        if abs(x - 0.5) < 0.04 or abs(y - 0.5) < 0.04:
            raise SpecError(f"items[{i}] '{it['label']}' sits on an axis line (ambiguous quadrant) — decide which side it's on (keep x, y ≥0.04 from 0.5)")
        px = round(_ITEM['x0'] + x * (_ITEM['x1'] - _ITEM['x0']), 1)
        py = round(_ITEM['y1'] - y * (_ITEM['y1'] - _ITEM['y0']), 1)
        r = 6 if i == focal else 4
        pts.append((it, px, py, r))
        obstacles.append((px - r, py - r, px + r, py + r))
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            if math.hypot(pts[i][1] - pts[j][1], pts[i][2] - pts[j][2]) < pts[i][3] + pts[j][3] + 4:
                raise SpecError(f"items '{pts[i][0]['label']}' and '{pts[j][0]['label']}' overlap — cluster them into one item or spread them")

    # quadrant tags
    qn = spec.get('quadrants', {})
    fq = None
    if focal is not None:
        fx, fy = items[focal]['x'], items[focal]['y']
        fq = ('t' if fy > 0.5 else 'b') + ('r' if fx > 0.5 else 'l')
    for q, (tx, ty, anchor) in {'tl': (X0, Y0 + 8, 'start'), 'tr': (X1, Y0 + 8, 'end'),
                                'bl': (X0, Y1, 'start'), 'br': (X1, Y1, 'end')}.items():
        s = qn.get(q)
        if not s:
            continue
        s = s.upper()
        w = text_width(s, 9, True) + len(s) * 1.62
        is_f = q == fq
        svg.text('labels', tx, ty, s, size=9, mono=True, fill=INK if is_f else MUTED, anchor=anchor, spacing='0.18em',
                 weight=600 if is_f else None)
        l = tx if anchor == 'start' else tx - w
        obstacles.append((l, ty - 9, l + w, ty + 2))

    # labels: right, left, above, below — first that clears axes, bounds, dots and other labels
    order = sorted(range(len(pts)), key=lambda i: (i != focal, i))
    for i in order:
        it, px, py, r = pts[i]
        is_f = i == focal
        w = text_width(it['label'], 11, weight=600 if is_f else 400)
        cands = [('start', px + r + 8, py + 4), ('end', px - r - 8, py + 4),
                 ('middle', px, py - r - 8), ('middle', px, py + r + 15)]
        own = (px - r, py - r, px + r, py + r)
        placed = None
        for anchor, lx, ly in cands:
            l = lx if anchor == 'start' else (lx - w if anchor == 'end' else lx - w / 2)
            box = (l, ly - 9, l + w, ly + 3)
            if box[0] < 24 or box[2] > 976 or box[1] < Y0 - 16 or box[3] > Y1 + 24:
                continue
            if box[0] - 2 < cx < box[2] + 2 or box[1] - 2 < cy < box[3] + 2:
                continue       # never cross an axis line
            if any(_overlap(box, o) for o in obstacles if o != own):
                continue
            placed = (anchor, lx, ly, box)
            break
        if not placed:
            raise SpecError(f"no room to label '{it['label']}' without crossing an axis or another label — "
                            f"shorten it, or move/cluster its neighbours")
        anchor, lx, ly, box = placed
        obstacles.append(box)
        svg.text('labels', lx, ly, it['label'], size=11, weight=600 if is_f else None, fill=INK if is_f else MUTED, anchor=anchor)
        svg.el('nodes', 'circle', cx=px, cy=py, r=r, fill=ACCENT if is_f else INK)

    k = keys(spec)
    if focal is not None:
        svg.key(f'dot:{ACCENT}', k.get('focal') or items[focal].get('note') or items[focal]['label'])
        svg.key(f'glyph:<circle cx="{{x}}" cy="{{y}}" r="3.5" fill="{INK}" transform="translate(8 0)"/>', k.get('rest', 'Candidate'))
    ly = 456
    svg.height = ly
    legend_note(svg, ly, spec.get('note') or 'position is a judgement call, not a measurement')
    return svg, ly


QUADRANT_EXAMPLE = {
    "type": "quadrant", "slug": "followup-debt",
    "title": "Follow-up tech debt · impact × effort",
    "desc": "Eight follow-ups left by the cache rollout placed by impact and effort; removing the legacy session store is the one to do next.",
    "axes": {"x": ["cheap", "costly"], "y": ["minor", "major"]},
    "quadrants": {"tl": "do next", "tr": "plan", "bl": "fill-in", "br": "skip"},
    "items": [
        {"label": "Drop legacy session store", "x": 0.2, "y": 0.86, "focal": True},
        {"label": "Cache-key versioning", "x": 0.36, "y": 0.66},
        {"label": "Shard the cache cluster", "x": 0.78, "y": 0.84},
        {"label": "Replace cron warmers", "x": 0.66, "y": 0.62},
        {"label": "Rename TTL flags", "x": 0.14, "y": 0.3},
        {"label": "Dashboard cleanup", "x": 0.34, "y": 0.14},
        {"label": "Rewrite the invalidation bus", "x": 0.7, "y": 0.28},
        {"label": "Port to Redis 8", "x": 0.86, "y": 0.1},
    ],
    "keys": {"focal": "Do next · unblocks v2.0", "rest": "Follow-up"},
}


# ---------- heatmap ----------

def _suffix(unit):
    if not unit:
        return ''
    return unit if unit == '%' else (' ' + unit if len(unit) <= 3 else '')


def render_heatmap(spec: dict):
    need(spec, 'rows', 'cols', 'values')
    rows, cols, vals = spec['rows'], spec['cols'], spec['values']
    if not (isinstance(rows, list) and isinstance(cols, list)):
        raise SpecError('"rows" and "cols" must be lists of labels')
    R, C = len(rows), len(cols)
    if R < 3 or C < 3:
        raise SpecError(f'{R} × {C} grid is too small — under 3 rows or columns a table says it with less ink')
    budget('heatmap rows', R, 7, 'split the rows into two heatmaps or aggregate')
    budget('heatmap columns', C, 8, 'aggregate periods (e.g. by month) or split')
    if not (isinstance(vals, list) and len(vals) == R and all(isinstance(r, list) and len(r) == C for r in vals)):
        raise SpecError(f'"values" must be a complete {R} × {C} grid (one list of {C} numbers per row) — '
                        f'never drop cells; a missing row reads as "no problem there"')
    grid = [[num(v, f'values[{i}][{j}] ({rows[i]} · {cols[j]})') for j, v in enumerate(r)] for i, r in enumerate(vals)]
    if any(v < 0 for r in grid for v in r):
        raise SpecError('negative values — the single ink ramp is for unsigned rates/counts; signed data needs a diverging design')
    fr = fc = None
    if spec.get('focal') is not None:
        f = spec['focal']
        if not (isinstance(f, list) and len(f) == 2):
            raise SpecError('"focal" must be [row, col] — indexes or labels — of the ONE cell the title is about')
        fr = f[0] if isinstance(f[0], int) else (rows.index(f[0]) if f[0] in rows else None)
        fc = f[1] if isinstance(f[1], int) else (cols.index(f[1]) if f[1] in cols else None)
        if fr is None or fc is None or not (0 <= fr < R and 0 <= fc < C):
            raise SpecError(f'"focal" {f} is not a cell of the grid — use [row, col] indexes or labels')

    unit = spec.get('unit', '')
    sfx = _suffix(unit)
    L = max(160, snap_up(max(text_width(str(r), 9, True) for r in rows) + 24))
    avail = 960 - L
    cw = min(116, int((avail - 4 * (C - 1)) / C))
    if cw < 80:
        raise SpecError(f'{C} columns leave {cw}px cells (< 80) — cut columns or shorten row labels')
    ch, T = 56, 64
    gw = C * cw + (C - 1) * 4
    gh = R * ch + (R - 1) * 4
    svg = Svg(width=1000, height=500)

    nf = [grid[i][j] for i in range(R) for j in range(C) if (i, j) != (fr, fc)]
    mx = max(nf) if nf else 0
    alpha = lambda v: round(max(0.07, (v / mx) * 0.65), 2) if mx > 0 else 0.07

    at = spec.get('axes', {})
    if at.get('cols'):
        svg.text('labels', L + gw / 2, 36, at['cols'].upper(), size=7, mono=True, fill=MUTED, anchor='middle', spacing='0.14em')
    if at.get('rows'):
        cy = T + gh / 2
        svg.el('labels', 'text', at['rows'].upper(), x=24, y=round(cy), fill=MUTED, font_size=7, font_family=MONO,
               letter_spacing='0.14em', text_anchor='middle', transform=f'rotate(-90 24 {round(cy)})')
    for j, c in enumerate(cols):
        s = str(c)
        if text_width(s, 9, True) + len(s) * 1.26 > cw - 4:
            raise SpecError(f"column label '{s}' is wider than its {cw}px cell — shorten it")
        svg.el('labels', 'text', s, data_axis=j, data_col=s, x=L + j * (cw + 4) + cw / 2, y=52, fill=MUTED, font_size=9,
               font_family=MONO, letter_spacing='0.14em', text_anchor='middle')
    for i, r in enumerate(rows):
        svg.el('labels', 'text', str(r), data_row_label=str(r), x=L - 12, y=T + i * (ch + 4) + ch / 2 + 4, fill=INK,
               font_size=9, font_family=MONO, text_anchor='end')

    fnote = spec.get('focal_note')
    for i in range(R):
        for j in range(C):
            x, y = L + j * (cw + 4), T + i * (ch + 4)
            v = grid[i][j]
            txt = fmt(v) + sfx
            if text_width(txt, 10, weight=600) > cw - 8:
                raise SpecError(f'value "{txt}" does not fit a {cw}px cell — drop the unit suffix or round')
            svg.el('nodes', 'rect', x=x, y=y, width=cw, height=ch, fill=PAPER)
            if (i, j) == (fr, fc):
                svg.el('nodes', 'rect', data_row=str(rows[i]), data_col=str(cols[j]), data_value=fmt(v), data_focal='true',
                       x=x, y=y, width=cw, height=ch, fill=tint('accent', 0.85), stroke=ACCENT, stroke_width=1.2)
                if fnote:
                    svg.text('labels', x + cw / 2, y + ch / 2 - 3, txt, size=10, weight=600, fill=PAPER, anchor='middle')
                    s = fnote.upper()
                    if text_width(s, 7, True) + len(s) * 0.42 > cw - 8:
                        raise SpecError(f'focal_note "{fnote}" is wider than the cell — keep it to ~{int((cw - 8) / 4.8)} chars')
                    svg.text('labels', x + cw / 2, y + ch / 2 + 11, s, size=7, mono=True, fill=PAPER, anchor='middle', spacing='0.06em')
                else:
                    svg.text('labels', x + cw / 2, y + ch / 2 + 4, txt, size=10, weight=600, fill=PAPER, anchor='middle')
            else:
                a = alpha(v)
                svg.el('nodes', 'rect', data_row=str(rows[i]), data_col=str(cols[j]), data_value=fmt(v),
                       x=x, y=y, width=cw, height=ch, fill=tint('ink', a))
                svg.text('labels', x + cw / 2, y + ch / 2 + 4, txt, size=8, mono=True, fill=PAPER if a >= 0.40 else INK, anchor='middle')

    k = keys(spec)
    lo = min(nf) if nf else 0
    key_ramp(svg, [0.07, 0.2, 0.35, 0.5, 0.65], k.get('rest', f'Low → high · {fmt(lo)}–{fmt(mx)}{sfx}' + (' (focal excluded)' if fr is not None else '')))
    if fr is not None:
        svg.key(f'swatch:{tint("accent", 0.85)}|{ACCENT}',
                k.get('focal', f'{rows[fr]} · {cols[fc]} · {fmt(grid[fr][fc])}{sfx}' + (f' — {fnote}' if fnote else '')))
    ly = snap_up(T + gh + 28)
    svg.height = ly
    unit_note = f' · values in {unit}' if unit and not sfx else ''
    legend_note(svg, ly, spec.get('note') or f'every {len(rows)} × {len(cols)} cell shown · one ink ramp{unit_note}')
    return svg, ly


HEATMAP_EXAMPLE = {
    "type": "heatmap", "slug": "ci-failures",
    "title": "The sprint payments went red",
    "desc": "CI failure rate by service and sprint; payments spiked to 41% in sprint 24 when the flaky contract tests landed, and every other cell stayed under 10%.",
    "unit": "%",
    "axes": {"rows": "service", "cols": "sprint"},
    "rows": ["auth", "payments", "api-gateway", "billing", "notifications"],
    "cols": ["S21", "S22", "S23", "S24", "S25", "S26"],
    "values": [
        [4, 5, 6, 3, 2, 2],
        [3, 4, 5, 41, 7, 4],
        [2, 3, 4, 2, 1, 1],
        [5, 7, 9, 6, 4, 3],
        [1, 2, 2, 2, 1, 1],
    ],
    "focal": ["payments", "S24"],
    "focal_note": "flaky tests",
}


TYPES = {
    'quadrant': (render_quadrant, QUADRANT_EXAMPLE, '2×2 of judged positions (impact × effort); ≤12 items, one focal'),
    'heatmap': (render_heatmap, HEATMAP_EXAMPLE, 'rows × cols grid (3–7 × 3–8) where one cell is the story; one ink ramp'),
}
