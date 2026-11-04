"""Stacked-hierarchy engines: `layers` (layer stack), `pyramid` (pyramid / funnel), `nested` (containment).

Layout grammar from diagram-design type-layers.md / type-pyramid.md / type-nested.md and
their example assets, recoloured to the explainer palette (coral → ACCENT, muted/ink tints → tint()).
"""
from __future__ import annotations

import math

from .core import (ACCENT, INK, MUTED, PAPER, SOFT, SpecError, Svg, budget, need, snap, text_width, tint)

W = 1000


def tw(s: str, size: float, mono: bool = False, weight: int = 400, spacing: float = 0.0) -> float:
    """text_width plus letter-spacing (em per glyph), which core's estimate leaves out."""
    return text_width(s, size, mono, weight) + len(str(s)) * spacing * size


def _n(v) -> str:
    return f'{v:.1f}'.rstrip('0').rstrip('.') if isinstance(v, float) else str(v)


def _one_focal(items: list, what: str, hint: str) -> int:
    idx = [i for i, it in enumerate(items) if it.get('focal')]
    if len(idx) != 1:
        raise SpecError(f'{what} needs exactly one "focal": true ({hint}); found {len(idx)}')
    return idx[0]


def _direction(svg: Svg, spec_dir, ax: float, top: float, bottom: float, what: str) -> None:
    """Left-margin direction indicator: hairline + arrowhead, mono eyebrow at the head, optional one at the tail."""
    if not spec_dir:
        return
    if not isinstance(spec_dir, dict) or spec_dir.get('arrow') not in ('up', 'down') or not spec_dir.get('label'):
        raise SpecError(f'{what} "direction" must be {{"arrow": "up"|"down", "label": "ABSTRACTION", "from"?: "HARDWARE"}}')
    up = spec_dir['arrow'] == 'up'
    svg.el('edges', 'line', x1=ax, y1=top + (8 if up else 0), x2=ax, y2=bottom - (0 if up else 8),
           stroke=tint('ink', 0.3), stroke_width=1)
    pts = f'{_n(ax - 4)},{top + 8} {_n(ax + 4)},{top + 8} {_n(ax)},{top}' if up else \
          f'{_n(ax - 4)},{bottom - 8} {_n(ax + 4)},{bottom - 8} {_n(ax)},{bottom}'
    svg.el('edges', 'polygon', points=pts, fill=MUTED)
    for text, at_top in ((spec_dir['label'], up), (spec_dir.get('from'), not up)):
        if not text:
            continue
        s = str(text).upper()
        w = tw(s, 8, True, spacing=0.18)
        x, anchor = (ax, 'middle') if ax - w / 2 >= 32 else (32, 'start')
        svg.text('labels', x, top - 12 if at_top else bottom + 20, s, size=8, mono=True, fill=MUTED, anchor=anchor, spacing='0.18em')


def _dir_room(spec_dir) -> tuple[int, int]:
    """(extra space above, below) the stack that the direction labels need."""
    if not spec_dir or not isinstance(spec_dir, dict):
        return 0, 0
    up = spec_dir.get('arrow') == 'up'
    head, tail = bool(spec_dir.get('label')), bool(spec_dir.get('from'))
    above = head if up else tail
    below = tail if up else head
    return (24 if above else 0), (24 if below else 0)


# ============================================================ layers

L_H = 64


def render_layers(spec: dict):
    need(spec, 'layers')
    layers = spec['layers']
    if not isinstance(layers, list):
        raise SpecError('layers "layers" must be a list of {"tag", "name", "note"?}, top layer first')
    if len(layers) < 3:
        raise SpecError(f'layers: {len(layers)} bands — a stack needs 4–6 (3 at the least); for fewer, use a table or an architecture diagram')
    budget('layers', len(layers), 6, 'merge adjacent layers or split into an overview + detail stack')
    fi = _one_focal(layers, 'layers', 'the layer under discussion')
    d = spec.get('direction')
    x0 = 128 if d else 80
    x1 = x0 + 840
    room_top, room_bot = _dir_room(d)
    y0 = 32 + room_top
    n = len(layers)
    y1 = y0 + n * L_H
    svg = Svg(width=W, height=y1 + room_bot + 32)

    name_x = x0 + 140
    for i, ly in enumerate(layers):
        for k in ('tag', 'name'):
            if not ly.get(k):
                raise SpecError(f'layers[{i}] needs "{k}" (index tag like "L3", and the layer name)')
        tag, name, note = str(ly['tag']).upper(), str(ly['name']), str(ly.get('note') or '')
        if tw(tag, 8, True, 600, 0.14) > 140 - 20 - 12:
            raise SpecError(f'layers[{i}] tag "{ly["tag"]}" is too wide for the index column (~13 chars max)')
        room = (x1 - 20) - name_x - 24
        need_w = tw(name, 16, weight=600) + (tw(note, 10, True, spacing=0.08) if note else 0)
        if need_w > room:
            raise SpecError(f'layers[{i}] "{name}": name + note are ~{int(need_w)}px, the band fits {room}px — shorten the note')
        y = y0 + i * L_H
        is_f = i == fi
        fill = tint('accent', 0.08) if is_f else (PAPER if i == 0 else tint('ink', min(0.06, 0.015 * i)))
        svg.el('zones', 'rect', x=x0, y=y, width=x1 - x0, height=L_H, fill=fill)
        if i < n - 1:
            svg.el('edges', 'line', x1=x0, y1=y + L_H, x2=x1, y2=y + L_H, stroke=tint('ink', 0.12), stroke_width=1)
        col = ACCENT if is_f else MUTED
        svg.text('labels', x0 + 20, y + 36, tag, size=8, mono=True, fill=col, weight=600 if is_f else None, spacing='0.14em')
        svg.text('labels', name_x, y + 36, name, size=16, weight=600, fill=INK)
        if note:
            svg.text('labels', x1 - 20, y + 36, note, size=10, mono=True, fill=col, anchor='end', spacing='0.08em')
    svg.el('nodes', 'rect', x=x0, y=y0, width=x1 - x0, height=y1 - y0, fill='none', stroke=MUTED, stroke_width=1)
    fy = y0 + fi * L_H
    svg.el('nodes', 'rect', x=x0, y=fy, width=x1 - x0, height=L_H, fill='none', stroke=ACCENT, stroke_width=1)
    _direction(svg, d, x0 - 48, y0, y1, 'layers')

    svg.key(f'swatch:{tint("accent", 0.08)}|{ACCENT}', str(spec.get('focal_label', 'Focal layer')))
    svg.key(f'swatch:{tint("ink", 0.03)}|{MUTED}', 'Layer')
    legend_y = y1 + room_bot + 24
    svg.height = legend_y
    return svg, legend_y


LAYERS_EXAMPLE = {
    'type': 'layers', 'slug': 'orders-request-path',
    'title': 'Orders request path · with the new repository layer',
    'desc': 'Layer stack of the orders service from HTTP router to Postgres, highlighting the repository layer this change inserts between handlers and the query layer.',
    'layers': [
        {'tag': 'L5', 'name': 'HTTP router', 'note': 'chi · /v2/orders/*'},
        {'tag': 'L4', 'name': 'Handlers', 'note': 'validate, map DTOs'},
        {'tag': 'L3', 'name': 'OrderRepository', 'note': 'new · owns tx + retries', 'focal': True},
        {'tag': 'L2', 'name': 'Query layer', 'note': 'sqlc-generated, pgx pool'},
        {'tag': 'L1', 'name': 'Postgres', 'note': 'orders, order_items'},
    ],
    'direction': {'arrow': 'down', 'from': 'CALLER', 'label': 'STORAGE'},
    'focal_label': 'New in this change',
}


# ============================================================ pyramid / funnel

P_H = 64
P_WMAX = 800


def _fmt_count(v: float) -> str:
    return f'{int(v):,}' if float(v).is_integer() else f'{v:,.4g}'


def render_pyramid(spec: dict):
    need(spec, 'layers')
    orient = spec.get('orientation', 'pyramid')
    if orient not in ('pyramid', 'funnel'):
        raise SpecError('pyramid "orientation" must be "pyramid" (point up) or "funnel" (point down)')
    layers = spec['layers']
    if not isinstance(layers, list) or len(layers) < 3:
        raise SpecError('pyramid needs 4–6 "layers" (3 at the least), listed top to bottom')
    budget('pyramid layers', len(layers), 6, 'compress adjacent layers — 7+ is illegible')
    n = len(layers)
    fi = _one_focal(layers, 'pyramid', 'the apex, the conversion stage or the bottleneck')
    base = n - 1 if orient == 'pyramid' else 0
    if fi == base:
        raise SpecError(f'focal is on the {"base" if orient == "pyramid" else "widest top stage"} ("{layers[fi].get("name")}"), '
                        f'which dilutes the signal — put it on the apex / conversion stage / bottleneck')
    for i, ly in enumerate(layers):
        if not ly.get('name'):
            raise SpecError(f'pyramid layers[{i}] needs "name"')

    has_v = [('value' in ly) for ly in layers]
    value_mode = any(has_v)
    if value_mode:
        if not all(has_v):
            raise SpecError('pyramid: give every layer a "value" (widths become proportional) or none (widths step linearly)')
        vals = []
        for i, ly in enumerate(layers):
            v = ly['value']
            if not isinstance(v, (int, float)) or isinstance(v, bool) or v <= 0:
                raise SpecError(f'pyramid layers[{i}].value must be a positive number (got {v!r})')
            vals.append(float(v))
        pairs = list(zip(vals, vals[1:]))
        if orient == 'pyramid' and any(b < a for a, b in pairs):
            raise SpecError('pyramid values must grow top → bottom (apex smallest); for a narrowing flow use "orientation": "funnel"')
        if orient == 'funnel' and any(b > a for a, b in pairs):
            raise SpecError('funnel values must shrink top → bottom; for a growing hierarchy use "orientation": "pyramid"')

    # text needs
    def text_need(ly):
        return max(tw(ly['name'], 12, weight=600), tw(ly.get('sub') or '', 9, True)) + 32

    sides = []
    for i, ly in enumerate(layers):
        s = ly.get('side')
        if s is None and value_mode:
            s = _fmt_count(vals[i])
            if orient == 'funnel' and i > 0:
                s += f' · −{round((1 - vals[i] / vals[i - 1]) * 100)}%'
        sides.append(str(s) if s else '')
    side_w = max(tw(s, 9, True, spacing=0.08) for s in sides) if any(sides) else 0
    d = spec.get('direction')
    axis_room = 56 if d else 0
    right_room = side_w + 16 if side_w else 0

    def edges_for(Wm: float):
        """n+1 boundary widths top → bottom, each a multiple of 8 so half-widths stay on the grid."""
        if value_mode:
            mids = vals
            e = [0.0] * (n + 1)
            for k in range(1, n):
                e[k] = (mids[k - 1] + mids[k]) / 2
            e[0] = max(0.0, mids[0] - (mids[1] - mids[0]) / 2)
            e[n] = max(0.0, mids[-1] + (mids[-1] - mids[-2]) / 2)
            s = Wm / max(e)
            e = [x * s for x in e]
        else:
            needs = [text_need(ly) for ly in layers]
            if orient == 'pyramid':        # edges grow top → bottom; layer i's narrow edge is e[i]
                lo = max([Wm * 0.2] + [(needs[i] - Wm * i / n) / (1 - i / n) for i in range(n)])
                e = [lo + (Wm - lo) * k / n for k in range(n + 1)]
            else:                          # edges shrink; layer i's narrow edge is e[i+1]
                lo = max([Wm * 0.2] + [Wm - (Wm - needs[i]) * n / (i + 1) for i in range(n)])
                e = [Wm - (Wm - lo) * k / n for k in range(n + 1)]
        return [min(Wm, max(0, round(x / 8) * 8)) for x in e]

    left_room = 0
    for _ in range(4):
        Wm = min(P_WMAX, math.floor((W - 64 - axis_room - left_room - right_room) / 8) * 8)
        if Wm < 320:
            raise SpecError('pyramid: names/side notes leave under 320px for the shape — shorten "side" and "sub" texts')
        e = edges_for(Wm)
        outside = [i for i, ly in enumerate(layers) if min(e[i], e[i + 1]) < text_need(ly)]
        if not value_mode and outside:
            raise SpecError(f'pyramid layer "{layers[outside[0]]["name"]}" can\'t fit its text — shorten name/sub')
        # text shown left of the shape: room needed beyond the shape's own left edge at that row
        need_left = 0
        for i in outside:
            tw_i = text_need(layers[i]) - 32
            need_left = max(need_left, tw_i + 16 - (Wm - max(e[i], e[i + 1])) / 2)
        new_left = max(0, math.ceil(need_left / 4) * 4)
        if new_left == left_room:
            break
        left_room = new_left

    used = axis_room + left_room + Wm + right_room
    off = snap((W - 64 - used) / 2)
    cx = snap(32 + off + axis_room + left_room + Wm / 2)
    room_top, room_bot = _dir_room(d)
    y0 = 32 + room_top
    y1 = y0 + n * P_H
    svg = Svg(width=W)

    def poly(i):
        t, b = e[i] / 2, e[i + 1] / 2
        y = y0 + i * P_H
        return [(cx - t, y), (cx + t, y), (cx + b, y + P_H), (cx - b, y + P_H)]

    pts = lambda ps: ' '.join(f'{_n(x)},{_n(y)}' for x, y in ps)  # noqa: E731
    for i, ly in enumerate(layers):
        dist = abs(i - (0 if orient == 'pyramid' else n - 1))        # 0 at the narrow end
        fill = tint('ink', round(0.02 + 0.04 * dist / max(1, n - 1), 3))
        svg.el('zones', 'polygon', points=pts(poly(i)), fill=fill, stroke=tint('ink', 0.12), stroke_width=1)
    outline = [poly(i)[1] for i in range(n)] + [poly(n - 1)[2], poly(n - 1)[3]] + [poly(i)[0] for i in range(n - 1, -1, -1)]
    svg.el('nodes', 'polygon', points=pts(outline), fill='none', stroke=MUTED, stroke_width=1)
    svg.el('nodes', 'polygon', points=pts(poly(fi)), fill=tint('accent', 0.08), stroke=ACCENT, stroke_width=1)

    for i, ly in enumerate(layers):
        y = y0 + i * P_H
        is_f = i == fi
        sub = ly.get('sub')
        widest = max(e[i], e[i + 1]) / 2
        if i in outside:
            x, anchor = cx - widest - 16, 'end'
        else:
            x, anchor = cx, 'middle'
        svg.text('labels', x, y + (28 if sub else 36), ly['name'], size=12, weight=600, fill=INK, anchor=anchor)
        if sub:
            svg.text('labels', x, y + 44, str(sub), size=9, mono=True, fill=MUTED, anchor=anchor)
        if sides[i]:
            svg.text('labels', cx + widest + 16, y + 36, sides[i], size=9, mono=True,
                     fill=ACCENT if is_f else SOFT, spacing='0.08em')
    _direction(svg, d, 32 + off + 16, y0, y1, 'pyramid')

    stage = 'stage' if orient == 'funnel' else 'layer'
    svg.key(f'swatch:{tint("accent", 0.08)}|{ACCENT}', str(spec.get('focal_label', f'Focal {stage}')))
    svg.key(f'swatch:{tint("ink", 0.04)}|{tint("ink", 0.25)}', stage.capitalize())
    if value_mode:
        svg.key('glyph:', 'Width is proportional to the value')
    legend_y = y1 + room_bot + 24
    svg.height = legend_y
    return svg, legend_y


PYRAMID_EXAMPLE = {
    'type': 'pyramid', 'slug': 'test-pyramid-after',
    'title': 'Checkout test suite after the contract-test split',
    'desc': 'Test pyramid for the checkout service after moving slow end-to-end checks into a new contract-test layer.',
    'orientation': 'pyramid',
    'layers': [
        {'name': 'End-to-end', 'sub': 'browser, staging', 'side': '18 tests · was 64'},
        {'name': 'Contract', 'sub': 'Pact, per consumer', 'side': '96 tests · new', 'focal': True},
        {'name': 'Integration', 'sub': 'service + real Postgres', 'side': '210 tests · was 180'},
        {'name': 'Unit', 'sub': 'pure functions, fakes', 'side': '1,240 tests · was 910'},
    ],
    'direction': {'arrow': 'up', 'label': 'SLOWER', 'from': 'FASTER'},
    'focal_label': 'New layer in this change',
}


# ============================================================ nested

N_INSET_X, N_INSET_Y = 32, 36


def render_nested(spec: dict):
    need(spec, 'levels')
    levels = spec['levels']
    if not isinstance(levels, list) or len(levels) < 3:
        raise SpecError('nested needs 3–5 "levels" (outer → inner); for two scopes, draw a single boundary in an architecture diagram')
    budget('nested levels', len(levels), 6, 'merge levels — detail disappears inward past 6')
    n = len(levels)
    for i, lv in enumerate(levels):
        if not lv.get('label'):
            raise SpecError(f'nested levels[{i}] needs "label" (the scope name shown on its border)')
    inner = levels[-1]
    iname, idesc = inner.get('name'), inner.get('desc')
    inner_h = 96 if (iname and idesc) else 72
    x, y = 32, 40
    w = W - 64
    h = inner_h + 2 * N_INSET_Y * (n - 1)
    svg = Svg(width=W, height=y + h + 32)

    outer_a = [0.30 + 0.20 * k / max(1, n - 3) for k in range(max(0, n - 2))]
    for k, lv in enumerate(levels):
        rx_, ry_ = x + k * N_INSET_X, y + k * N_INSET_Y
        rw, rh = w - 2 * k * N_INSET_X, h - 2 * k * N_INSET_Y
        focal = k == n - 1
        if focal:
            stroke, fill, lab_fill = ACCENT, tint('accent', 0.06), ACCENT
        elif k == n - 2:
            stroke, fill, lab_fill = MUTED, tint('ink', 0.03), INK
        else:
            stroke, fill, lab_fill = tint('ink', round(outer_a[k], 2)), tint('ink', round(0.015 + 0.005 * k, 3)), MUTED
        svg.el('zones', 'rect', x=rx_, y=ry_, width=rw, height=rh, rx=8, fill=fill, stroke=stroke, stroke_width=1)
        lab = str(lv['label'])
        lw = math.ceil((tw(lab, 8, True, 600 if focal else 400, 0.14) + 16) / 4) * 4
        if lw > rw - 48:
            raise SpecError(f'nested levels[{k}] label "{lab}" is wider than its ring — shorten it')
        svg.el('labels', 'rect', x=rx_ + 16, y=ry_ - 8, width=lw, height=16, fill=PAPER)
        svg.text('labels', rx_ + 24, ry_ + 4, lab, size=8, mono=True, fill=lab_fill, weight=600 if focal else None, spacing='0.14em')
        desc = lv.get('desc')
        if desc and not focal:
            dw = tw(desc, 9, True)
            if dw > rw - lw - 64:
                raise SpecError(f'nested levels[{k}] desc "{desc}" is ~{int(dw)}px; the ring band fits {int(rw - lw - 64)}px — shorten it')
            svg.text('labels', rx_ + rw - 16, ry_ + 20, desc, size=9, mono=True, fill=SOFT, anchor='end')
        if focal:
            cxm, cym = rx_ + rw / 2, ry_ + rh / 2
            for s, sz, mono, wt in ((iname, 16, False, 600), (idesc, 9, True, 400)):
                if s and tw(s, sz, mono, wt) > rw - 48:
                    raise SpecError(f'innermost text "{s}" is wider than the focal ring ({rw - 48}px) — shorten it')
            if iname and idesc:
                svg.text('labels', cxm, cym - 4, iname, size=16, weight=600, fill=INK, anchor='middle')
                svg.text('labels', cxm, cym + 16, idesc, size=9, mono=True, fill=MUTED, anchor='middle', spacing='0.06em')
            elif iname:
                svg.text('labels', cxm, cym + 6, iname, size=16, weight=600, fill=INK, anchor='middle')
            elif idesc:
                svg.text('labels', cxm, cym + 4, idesc, size=10, mono=True, fill=MUTED, anchor='middle', spacing='0.06em')

    svg.key(f'swatch:{tint("accent", 0.06)}|{ACCENT}', str(spec.get('focal_label', 'Focal scope')))
    svg.key(f'swatch:{tint("ink", 0.02)}|{tint("ink", 0.35)}', 'Enclosing scope')
    legend_y = y + h + 32
    svg.height = legend_y
    return svg, legend_y


NESTED_EXAMPLE = {
    'type': 'nested', 'slug': 'v2-writes-blast-radius',
    'title': 'Blast radius of the orders.v2_writes flag',
    'desc': 'Nested scopes showing that flipping orders.v2_writes reaches only the dual-write path of orders-api pods in the eu-west-1 canary region.',
    'levels': [
        {'label': 'prod · all regions', 'desc': 'flag pushed by config-service'},
        {'label': 'eu-west-1', 'desc': 'canary region · 10% of traffic'},
        {'label': 'orders-api', 'desc': '12 pods hot-reload the flag'},
        {'label': 'OrderRepository.save()', 'name': 'Dual-write path', 'desc': 'writes go to both tables; reads untouched'},
    ],
    'focal_label': 'What the flag actually changes',
}


TYPES = {
    'layers': (render_layers, LAYERS_EXAMPLE,
               'stacked abstraction levels with one focal layer — where a new layer sits in the call path'),
    'pyramid': (render_pyramid, PYRAMID_EXAMPLE,
                'ranked hierarchy or narrowing funnel — test pyramid shift, request funnel with real counts'),
    'nested': (render_nested, NESTED_EXAMPLE,
               'scopes inside scopes, innermost focal — blast radius of a config or permission change'),
}
