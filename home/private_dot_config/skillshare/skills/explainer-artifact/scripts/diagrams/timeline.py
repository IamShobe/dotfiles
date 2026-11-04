"""Time-axis engines: `timeline` (events on an honest time scale) and `gantt` (phased task plan).

Layout grammar from diagram-design type-timeline.md / type-gantt.md and their example
assets, recoloured to the explainer palette (coral → ACCENT, muted/ink tints → tint()).
"""
from __future__ import annotations

import datetime as dt
import math
import re

from .core import (ACCENT, INK, MUTED, PAPER, SOFT, SpecError, Svg, budget, need, snap, text_width, tint)

W = 1000
MONTHS = ('JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC')


def tw(s: str, size: float, mono: bool = False, weight: int = 400, spacing: float = 0.0) -> float:
    """text_width plus letter-spacing (em per glyph), which core's estimate leaves out."""
    return text_width(s, size, mono, weight) + len(str(s)) * spacing * size


def _glyph(inner: str) -> str:
    """Legend glyph drawn in a local frame whose origin is the swatch's left-middle point."""
    return 'glyph:<g transform="translate({x},{y})">' + inner + '</g>'


# ============================================================ timeline

# numeric-axis unit → tick-label prefix
NUM_PREFIX = {'week': 'W', 'day': 'D', 'sprint': 'S', 'month': 'M', 'quarter': 'Q', 'release': 'R', 'number': ''}
DATE_UNITS = ('day', 'week', 'month', 'quarter', 'year')
_ISO = re.compile(r'^(\d{4})-(\d{2})(?:-(\d{2}))?$')


def _parse_time(v, what: str):
    """→ (kind, value, precision): kind 'n' (plain number) or 'd' (date ordinal)."""
    if isinstance(v, bool):
        v = None
    if isinstance(v, (int, float)):
        return 'n', float(v), 'n'
    if isinstance(v, str):
        s = v.strip()
        if re.fullmatch(r'-?\d+(\.\d+)?', s):
            return 'n', float(s), 'n'
        m = _ISO.match(s)
        if m:
            y, mo, d = int(m[1]), int(m[2]), int(m[3] or 1)
            try:
                return 'd', float(dt.date(y, mo, d).toordinal()), 'day' if m[3] else 'month'
            except ValueError:
                pass
    raise SpecError(f'{what} = {v!r} is not a time — use an ISO date ("2026-03-15" or "2026-03") '
                    f'or a plain number (week 3 → 3)')


def _date_ticks(a: float, b: float, unit: str):
    """Tick ordinals + labels at unit boundaries within [a, b]."""
    d0, d1 = dt.date.fromordinal(int(math.ceil(a))), dt.date.fromordinal(int(b))
    out = []
    if unit in ('day', 'week'):
        d = d0
        if unit == 'week':
            d = d0 + dt.timedelta(days=(7 - d0.weekday()) % 7)      # Mondays
        step = 7 if unit == 'week' else 1
        while d <= d1:
            out.append((d.toordinal(), f'{MONTHS[d.month - 1]} {d.day:02d}'))
            d += dt.timedelta(days=step)
        return out
    months = {'month': 1, 'quarter': 3, 'year': 12}[unit]
    y, m = d0.year, d0.month
    while (m - 1) % months:
        m += 1
    if dt.date(y + (m - 1) // 12, (m - 1) % 12 + 1, 1) < d0:
        m += months
    first = True
    while True:
        yy, mm = y + (m - 1) // 12, (m - 1) % 12 + 1
        d = dt.date(yy, mm, 1)
        if d > d1:
            break
        yr = f"'{yy % 100:02d}"
        if unit == 'month':
            lab = f'{MONTHS[mm - 1]} {yr}' if (mm == 1 or first) else MONTHS[mm - 1]
        elif unit == 'quarter':
            lab = f'Q{(mm - 1) // 3 + 1} {yr}'
        else:
            lab = str(yy)
        out.append((d.toordinal(), lab))
        first = False
        m += months
    return out


def _fmt_num(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else f'{v:g}'


def render_timeline(spec: dict):
    need(spec, 'axis', 'events')
    axis, events = spec['axis'], spec['events']
    if not isinstance(axis, dict):
        raise SpecError('timeline "axis" must be an object: {"unit": "month", "start": "2026-01", "end": "2026-10"}')
    need({**axis, 'type': 'timeline axis'}, 'unit', 'start', 'end')
    if not isinstance(events, list) or not events:
        raise SpecError('timeline "events" must be a non-empty list of {"date", "label"}')
    budget('timeline events', len(events), 10, 'split the range into two timelines, or drop minor events')
    majors = sum(1 for e in events if e.get('major'))
    budget('major events (accent)', majors, 2, 'mark at most two events "major": true')

    unit = str(axis['unit']).lower()
    unit = 'day' if unit == 'date' else unit
    ka, a, _ = _parse_time(axis['start'], 'axis.start')
    kb, b, _ = _parse_time(axis['end'], 'axis.end')
    if ka != kb:
        raise SpecError('axis.start and axis.end must both be ISO dates or both plain numbers')
    if b <= a:
        raise SpecError(f'axis.end ({axis["end"]}) must be after axis.start ({axis["start"]})')
    if ka == 'd' and unit not in DATE_UNITS:
        raise SpecError(f'axis.unit "{unit}" can\'t tick a date axis — use one of: {", ".join(DATE_UNITS)}')
    if ka == 'n' and unit not in NUM_PREFIX:
        raise SpecError(f'axis.unit "{unit}" unknown for a numeric axis — use one of: {", ".join(NUM_PREFIX)}')

    x0, x1 = 112, 936
    px = lambda t: snap(x0 + (t - a) / (b - a) * (x1 - x0))  # noqa: E731

    # ticks at unit boundaries
    if ka == 'd':
        ticks = _date_ticks(a, b, unit)
    else:
        pre = NUM_PREFIX[unit]
        ticks = [(float(i), f'{pre}{i}') for i in range(int(math.ceil(a)), int(math.floor(b)) + 1)]
    step = 1
    while len(ticks) > 1 and (x1 - x0) / max(1, (len(ticks) - 1)) * step < 16:
        step += 1
    ticks = ticks[::step]
    lab_step = 1
    if len(ticks) > 1:
        pitch = abs(px(ticks[1][0]) - px(ticks[0][0])) or 1
        widest = max(tw(t[1], 8, True, spacing=0.14) for t in ticks)
        lab_step = max(1, math.ceil((widest + 12) / pitch))

    # event blocks
    items = []
    for i, e in enumerate(events):
        if not isinstance(e, dict) or 'date' not in e or not e.get('label'):
            raise SpecError(f'events[{i}] needs "date" and "label"')
        k, t, prec = _parse_time(e['date'], f'events[{i}].date')
        if k != ka:
            raise SpecError(f'events[{i}].date "{e["date"]}" must use the same kind of time as the axis')
        if not a <= t <= b:
            raise SpecError(f'events[{i}] "{e["label"]}" ({e["date"]}) is outside the axis {axis["start"]} → {axis["end"]} — widen the axis')
        if 'tag' in e:
            tag = str(e['tag'])
        elif k == 'd':
            d = dt.date.fromordinal(int(t))
            tag = f'{MONTHS[d.month - 1]} {d.day:02d}' if prec == 'day' else f'{MONTHS[d.month - 1]} {d.year}'
        else:
            tag = f'{NUM_PREFIX[unit]}{_fmt_num(t)}'
        major = bool(e.get('major'))
        lines = [(tag.upper(), 8, True, 400, 0.14, ACCENT if major else MUTED),
                 (e['label'], 14 if major else 12, False, 600, 0, INK)]
        if e.get('sub'):
            lines.append((e['sub'], 9, True, 400, 0, MUTED))
        w = max(tw(s, sz, mo, wt, sp) for s, sz, mo, wt, sp, _ in lines)
        if w > 280:
            raise SpecError(f'events[{i}] "{e["label"]}": text is ~{int(w)}px wide (max 280) — shorten the label/sub')
        items.append(dict(x=px(t), t=t, lines=lines, w=w, major=major, label=e['label']))

    def block(it, side, d):
        """Baselines + bounding rect (relative to the axis at y=0) for a block at drop length d."""
        lines = it['lines']
        gaps = [0] + [20 if lines[j][1] == 14 else 16 for j in range(1, len(lines))]
        if side > 0:   # below: first line (date tag) 16px under the drop's end
            first = d + 16
        else:          # above: last line 12px over the drop's end
            first = -d - 12 - sum(gaps)
        ys = [first + sum(gaps[:j + 1]) for j in range(len(lines))]
        lo, hi = 32 + it['w'] / 2, W - 32 - it['w'] / 2
        cx = it['x']
        if cx < lo:
            cx = math.ceil(lo / 4) * 4
        elif cx > hi:
            cx = math.floor(hi / 4) * 4
        top = ys[0] - lines[0][1]
        bot = ys[-1] + 3
        return ys, cx, (cx - it['w'] / 2, top, cx + it['w'] / 2, bot)

    placed = []   # (item, side, d, ys, cx, rect)

    def ok(it, side, d, rect):
        x, (l, t_, r, bm) = it['x'], rect
        seg = (min(0, side * d), max(0, side * d))
        for o in placed:
            ol, ot, or_, ob = o[5]
            if l < or_ + 12 and ol < r + 12 and t_ < ob + 8 and ot < bm + 8:
                return False
            if ol - 4 <= x <= or_ + 4 and seg[0] < ob and ot < seg[1]:          # my drop crosses its text
                return False
            ox, oseg = o[0]['x'], (min(0, o[1] * o[2]), max(0, o[1] * o[2]))
            if l - 4 <= ox <= r + 4 and oseg[0] < bm and t_ < oseg[1]:        # its drop crosses my text
                return False
        return True

    TIERS = (56, 120, 184)
    for i, it in enumerate(items):
        pref = -1 if i % 2 == 0 else 1
        for d in TIERS:
            done = False
            for side in (pref, -pref):
                ys, cx, rect = block(it, side, d)
                if ok(it, side, d, rect):
                    placed.append((it, side, d, ys, cx, rect))
                    done = True
                    break
            if done:
                break
        else:
            raise SpecError(f'event "{it["label"]}" collides with its neighbours on every tier — '
                            f'shorten labels, drop "sub", widen the axis range, or split the timeline')

    top = min([-12] + [p[5][1] for p in placed])
    bottom = max([28] + [p[5][3] for p in placed])
    Y = snap(32 - top + 2)
    svg = Svg(width=W, height=snap(Y + bottom + 32))

    # axis
    svg.el('edges', 'line', x1=x0, y1=Y, x2=x1, y2=Y, stroke=tint('muted', 0.45), stroke_width=1)
    unit_name = {'day': 'DAYS', 'week': 'WEEKS', 'month': 'MONTHS', 'quarter': 'QUARTERS', 'year': 'YEARS',
                 'sprint': 'SPRINTS', 'release': 'RELEASES', 'number': str(axis.get('label', 'UNITS')).upper()}[unit]
    svg.text('labels', x0 - 16, Y + 4, unit_name, size=8, mono=True, fill=SOFT, anchor='end', spacing='0.14em')
    tick_xs = {x0, x1} | {px(t) for t, _ in ticks}
    for x in sorted(tick_xs):
        svg.el('edges', 'line', x1=x, y1=Y - 8, x2=x, y2=Y + 8, stroke=tint('ink', 0.2), stroke_width=1)
    below_drops = [p[0]['x'] for p in placed if p[1] > 0]
    for j, (t, lab) in enumerate(ticks):
        if j % lab_step:
            continue
        x, hw = px(t), tw(lab, 8, True, spacing=0.14) / 2
        if any(abs(dx - x) < hw + 4 for dx in below_drops):
            continue    # a drop line would cut through it; the event's own date tag says when
        svg.text('labels', x, Y + 20, lab, size=8, mono=True, fill=SOFT, anchor='middle', spacing='0.14em')

    # events
    for it, side, d, ys, cx, rect in sorted(placed, key=lambda p: p[0]["major"]):   # majors paint on top
        x, major = it['x'], it['major']
        svg.el('edges', 'line', x1=x, y1=Y, x2=x, y2=Y + side * d, stroke=ACCENT if major else tint('ink', 0.3), stroke_width=1)
        svg.el('nodes', 'circle', cx=x, cy=Y, r=6 if major else 4, fill=ACCENT if major else INK)
        for (s, sz, mono, wt, sp, fill), y in zip(it['lines'], ys):
            svg.text('labels', cx, Y + y, s, size=sz, mono=mono, weight=wt if wt >= 600 else None, fill=fill,
                     anchor='middle', spacing=f'{sp}em' if sp else None)

    if any(not it['major'] for it in items):
        svg.key(_glyph(f'<circle cx="8" cy="0" r="4" fill="{INK}"/>'), 'Event')
    if majors:
        svg.key(_glyph(f'<circle cx="8" cy="0" r="6" fill="{ACCENT}"/>'), str(spec.get('major_label', 'Major milestone')))
    svg.key('glyph:', 'Spacing is proportional to real elapsed time')
    legend_y = snap(Y + bottom + 16)
    svg.height = legend_y
    return svg, legend_y


TIMELINE_EXAMPLE = {
    'type': 'timeline', 'slug': 'v1-api-sunset',
    'title': 'Sunsetting the v1 REST API',
    'desc': 'Deprecation schedule for the v1 REST API, from the v2 launch through warnings and brownouts to removal in September.',
    'axis': {'unit': 'month', 'start': '2026-01-01', 'end': '2026-10-01'},
    'events': [
        {'date': '2026-01-12', 'label': 'v2 API GA', 'sub': 'feature parity'},
        {'date': '2026-02-02', 'label': 'Deprecation announced', 'major': True, 'sub': 'changelog + email'},
        {'date': '2026-03-02', 'label': 'Sunset headers on v1', 'sub': 'Deprecation: true'},
        {'date': '2026-04-15', 'label': 'SDK logs warnings'},
        {'date': '2026-06-01', 'label': 'Weekly brownouts', 'sub': '1h, 503 + link'},
        {'date': '2026-07-15', 'label': 'v1 read-only'},
        {'date': '2026-09-01', 'label': 'v1 removed', 'major': True, 'sub': 'routes return 410'},
    ],
}


# ============================================================ gantt

G_LABEL_X, G_X0, G_X1 = 20, 200, 960          # type-gantt.md: label column 20–200, timeline 200–960
G_ROW, G_BAR, G_HEAD_Y, G_SEP_Y = 40, 24, 56, 64
UNIT_PREFIX = {'week': 'W', 'day': 'D', 'sprint': 'S', 'month': 'M', 'quarter': 'Q'}


def render_gantt(spec: dict):
    need(spec, 'total', 'phases')
    unit = str(spec.get('unit', 'week')).lower()
    if unit not in UNIT_PREFIX:
        raise SpecError(f'gantt "unit" must be one of: {", ".join(UNIT_PREFIX)}')
    total = spec['total']
    if not isinstance(total, int) or isinstance(total, bool) or not 1 <= total <= 52:
        raise SpecError(f'gantt "total" must be a whole number of {unit}s, 1–52 (got {total!r})')
    phases = spec['phases']
    if not isinstance(phases, list) or not phases:
        raise SpecError('gantt "phases" must be a non-empty list of {"label", "tasks": [...]}')
    tasks = [t for p in phases for t in (p.get('tasks') or [])]
    budget('gantt tasks', len(tasks), 12, 'collapse into a phase-level view or split into sub-plans')
    focal = [t for t in tasks if t.get('focal')]
    if len(focal) != 1:
        raise SpecError(f'gantt needs exactly one "focal": true task (the key deliverable / critical path); found {len(focal)}')
    pitch = (G_X1 - G_X0) / total
    X = lambda u: round(G_X0 + u * pitch)  # noqa: E731  (u = units elapsed from the start)

    for pi, p in enumerate(phases):
        if not p.get('tasks'):
            raise SpecError(f'phases[{pi}] has no tasks')
        cover = [0] * (total + 1)
        for ti, t in enumerate(p['tasks']):
            if not t.get('name'):
                raise SpecError(f'phases[{pi}].tasks[{ti}] needs "name"')
            s, e = t.get('start'), t.get('end')
            if not all(isinstance(v, int) and not isinstance(v, bool) for v in (s, e)) or not 1 <= s <= e <= total:
                raise SpecError(f'task "{t["name"]}": "start"/"end" are {unit} numbers, 1 ≤ start ≤ end ≤ {total} '
                                f'(end inclusive: start 2, end 3 = {UNIT_PREFIX[unit]}2–{UNIT_PREFIX[unit]}3); got {s!r}–{e!r}')
            nw = tw(t['name'], 11, weight=600)
            if nw > 172:
                raise SpecError(f'task name "{t["name"]}" is ~{int(nw)}px; the label column fits 172px (~26 chars) — shorten it')
            for u in range(s, e + 1):
                cover[u] += 1
        budget(f'parallel tracks in phase "{p.get("label", pi)}"', max(cover), 5, 'split the phase')

    svg = Svg(width=W)

    # rows + zones
    y, rows, zones = G_SEP_Y + 8, [], []
    draw_zones = len(phases) > 1 or bool(phases[0].get('label'))
    for p in phases:
        z_top = y
        for t in p['tasks']:
            rows.append((y + 12, t))
            y += G_ROW
        z_bot = y + 12 - 4          # last bar bottom + 8
        zones.append((z_top, z_bot, p.get('label')))
        y = z_bot + 12
    bottom = zones[-1][1]

    for z_top, z_bot, lab in zones:
        if draw_zones:
            svg.el('zones', 'rect', x=12, y=z_top, width=W - 24, height=z_bot - z_top, rx=6, fill=tint('ink', 0.02),
                   stroke=tint('ink', 0.10), stroke_width=0.8)
        if lab:
            svg.text('zones', G_LABEL_X, z_top + 12, str(lab).upper(), size=7, mono=True, fill=tint('ink', 0.4), spacing='0.14em')

    # time axis header
    labels = spec.get('labels')
    svg.text('labels', G_LABEL_X, G_HEAD_Y, f'{unit.upper()}S', size=8, mono=True, fill=SOFT, spacing='0.14em')
    group_edges = set()
    if labels and isinstance(labels[0], dict):
        spans = [int(g.get('span', 0)) for g in labels]
        if sum(spans) != total or min(spans) < 1:
            raise SpecError(f'grouped "labels" need "span" ≥ 1 each, summing to total ({total}); got {sum(spans)}')
        u = 0
        for g, sp in zip(labels, spans):
            mid = snap((X(u) + X(u + sp)) / 2)
            if tw(g.get('label', ''), 9, weight=600) > sp * pitch - 8:
                raise SpecError(f'header "{g.get("label")}" is wider than its {sp} {unit}(s) — shorten it or widen the span')
            svg.text('labels', mid, G_HEAD_Y, str(g.get('label', '')), size=9, weight=600, fill=INK, anchor='middle')
            u += sp
            if u < total:
                group_edges.add(u)
    else:
        if labels is not None and (not isinstance(labels, list) or len(labels) != total):
            raise SpecError(f'"labels" must list one label per {unit} ({total}), or be [{{"label", "span"}}] groups')
        labels = [str(s) for s in labels] if labels else [f'{UNIT_PREFIX[unit]}{i + 1}' for i in range(total)]
        widest = max(tw(s, 8, True, spacing=0.06) for s in labels)
        k = max(1, math.ceil((widest + 8) / pitch))
        for i, s in enumerate(labels):
            if i % k == 0:
                svg.text('labels', snap((X(i) + X(i + 1)) / 2), G_HEAD_Y, s, size=8, mono=True, fill=SOFT, anchor='middle', spacing='0.06em')
    for u in range(1, total):
        if u in group_edges:
            svg.el('edges', 'line', x1=X(u), y1=G_HEAD_Y - 16, x2=X(u), y2=bottom, stroke=tint('ink', 0.12),
                   stroke_width=0.8, stroke_dasharray='3,3')
        elif pitch >= 8:
            svg.el('edges', 'line', x1=X(u), y1=G_SEP_Y, x2=X(u), y2=bottom, stroke=tint('ink', 0.05), stroke_width=0.6)
    svg.el('edges', 'line', x1=G_X0, y1=G_SEP_Y, x2=G_X1, y2=G_SEP_Y, stroke=tint('ink', 0.2), stroke_width=0.8)
    svg.el('edges', 'line', x1=G_X0, y1=G_HEAD_Y - 16, x2=G_X0, y2=bottom, stroke=tint('ink', 0.2), stroke_width=0.8)

    # bars
    for ry, t in rows:
        is_f = bool(t.get('focal'))
        fill, stroke = (tint('accent', 0.12), ACCENT) if is_f else (tint('muted', 0.15), MUTED)
        bx, bw = X(t['start'] - 1), X(t['end']) - X(t['start'] - 1)
        svg.text('labels', G_LABEL_X, ry + 24, t['name'], size=11, weight=600, fill=ACCENT if is_f else INK)
        svg.el('nodes', 'rect', x=bx, y=ry + 8, width=bw, height=G_BAR, rx=4, fill=PAPER)
        svg.el('nodes', 'rect', x=bx, y=ry + 8, width=bw, height=G_BAR, rx=4, fill=fill, stroke=stroke, stroke_width=1)
        if t.get('note'):
            s = str(t['note']).upper()
            nw = tw(s, 9, True, spacing=0.06)
            col = ACCENT if is_f else MUTED
            if nw + 12 <= bw:
                svg.text('labels', snap(bx + bw / 2), ry + 24, s, size=9, mono=True, fill=col, anchor='middle', spacing='0.06em')
            elif bx + bw + 8 + nw <= G_X1:
                svg.text('labels', bx + bw + 8, ry + 24, s, size=9, mono=True, fill=col, spacing='0.06em')
            elif bx - 8 - nw >= G_X0 + 4:
                svg.text('labels', bx - 8, ry + 24, s, size=9, mono=True, fill=col, anchor='end', spacing='0.06em')
            else:
                raise SpecError(f'task "{t["name"]}": note "{t["note"]}" fits neither in nor beside its bar — shorten it')

    svg.key(f'swatch:{tint("accent", 0.12)}|{ACCENT}', str(spec.get('focal_label', f'{focal[0]["name"]} · focal')))
    if len(tasks) > 1:
        svg.key(f'swatch:{tint("muted", 0.15)}|{MUTED}', 'Task')
    if draw_zones:
        svg.key(f'swatch:{tint("ink", 0.02)}|{tint("ink", 0.10)}', 'Phase')

    end_y = bottom
    m = spec.get('marker')
    if m:
        if not isinstance(m, dict) or 'at' not in m:
            raise SpecError('gantt "marker" must be {"at": <unit number>, "label": "TODAY"}')
        at = m['at']
        if not isinstance(at, (int, float)) or isinstance(at, bool) or not 1 <= at <= total + 1:
            raise SpecError(f'marker.at is the {unit} whose start it marks, 1–{total + 1} (got {at!r})')
        mx = X(at - 1)
        lab = str(m.get('label', 'today'))
        svg.el('labels', 'line', x1=mx, y1=G_SEP_Y, x2=mx, y2=bottom + 8, stroke=MUTED, stroke_width=1, stroke_dasharray='4,3')
        lw = tw(lab.upper(), 8, True, spacing=0.06) + 8
        lx = min(max(mx, 32 + lw / 2), W - 32 - lw / 2)
        svg.label(lx, bottom + 24, lab, fill=MUTED)
        svg.key(_glyph(f'<line x1="0" y1="0" x2="22" y2="0" stroke="{MUTED}" stroke-width="1" stroke-dasharray="4,3"/>'),
                str(m.get('legend', 'Today / milestone')))
        end_y = bottom + 28
    legend_y = snap(end_y + 24) if end_y % 4 == 0 else snap(end_y + 26)
    svg.height = legend_y
    return svg, legend_y


GANTT_EXAMPLE = {
    'type': 'gantt', 'slug': 'orders-table-migration',
    'title': 'Orders table migration · 10-week plan',
    'desc': 'Ten-week plan moving orders to the new schema: dual-write, backfill and parity checks, then the read cutover and cleanup.',
    'unit': 'week', 'total': 10,
    'phases': [
        {'label': 'Prepare', 'tasks': [
            {'name': 'Ship new schema', 'start': 1, 'end': 1},
            {'name': 'Dual-write in service', 'start': 2, 'end': 3},
        ]},
        {'label': 'Backfill', 'tasks': [
            {'name': 'Backfill history', 'start': 3, 'end': 5, 'note': '~40M rows'},
            {'name': 'Verify parity', 'start': 5, 'end': 6, 'note': 'shadow reads'},
        ]},
        {'label': 'Cutover', 'tasks': [
            {'name': 'Switch reads to new table', 'start': 7, 'end': 7, 'focal': True, 'note': 'cutover'},
            {'name': 'Stop dual-write', 'start': 8, 'end': 8},
            {'name': 'Drop legacy table', 'start': 9, 'end': 10},
        ]},
    ],
    'marker': {'at': 7, 'label': 'today'},
}


TYPES = {
    'timeline': (render_timeline, TIMELINE_EXAMPLE,
                 'events on an honest time axis — deprecation schedule, release history, incident log'),
    'gantt': (render_gantt, GANTT_EXAMPLE,
              'phased plan of tasks over weeks — migration or rollout with overlap and one critical task'),
}
