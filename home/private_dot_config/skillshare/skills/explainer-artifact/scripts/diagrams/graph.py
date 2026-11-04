"""Graph engine: boxes on a grid joined by orthogonal connectors.

Types: architecture, flowchart, dependency, deployment, tree, org-chart, state, er,
db-schema, uml-class. They share one layout (nodes in grid cells, zones around node
groups) and one router (orthogonal L/Z routes that avoid every box, fanned attach
points, slotted channels, masked labels that dodge nodes and each other). Each type
adds its own node shapes and edge vocabulary.

Placement is the author's editorial choice: give nodes {"col", "row"}. Nodes without
them are auto-placed by rank (longest path from sources) along "direction".
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .core import (ACCENT, INK, LINK, MUTED, NODE_KINDS, PAPER, RULE, SOFT, SpecError, Svg, _n, budget, draw_edge,
                   fit_width, need, node_box, ortho_path, snap, snap_up, text_width, tint, zone)

# ---------------------------------------------------------------- model


@dataclass
class N:
    id: str
    w: int
    h: int
    col: int = 0
    row: int = 0
    x: float = 0
    y: float = 0
    shape: str = 'box'            # box | pill | diamond | dot | ring | record
    data: dict = field(default_factory=dict)

    @property
    def cx(self): return self.x + self.w / 2

    @property
    def cy(self): return self.y + self.h / 2

    def side(self, s: str, t: float = 0.5) -> tuple[float, float]:
        """Point on side s ('l','r','t','b') at fraction t along it."""
        if self.shape in ('diamond', 'dot', 'ring'):   # vertices only
            return {'l': (self.x, self.cy), 'r': (self.x + self.w, self.cy),
                    't': (self.cx, self.y), 'b': (self.cx, self.y + self.h)}[s]
        if s == 'l': return (self.x, self.y + self.h * t)
        if s == 'r': return (self.x + self.w, self.y + self.h * t)
        if s == 't': return (self.x + self.w * t, self.y)
        return (self.x + self.w * t, self.y + self.h)


@dataclass
class E:
    a: str
    b: str
    style: str = 'default'
    label: str | None = None
    data: dict = field(default_factory=dict)
    sa: str = ''                  # chosen sides
    sb: str = ''
    route: str = ''               # H | V | HV | VH | HVH | VHV
    pa: tuple | None = None       # attach points
    pb: tuple | None = None
    channel: float | None = None
    points: list = field(default_factory=list)


OPP = {'l': 'r', 'r': 'l', 't': 'b', 'b': 't'}


def _rect(n: N, pad: float = 0):
    return (n.x - pad, n.y - pad, n.x + n.w + pad, n.y + n.h + pad)


def _seg_hits(p, q, r) -> bool:
    """Axis-aligned segment p→q intersects rect r=(x0,y0,x1,y1)?"""
    x0, y0, x1, y1 = r
    if p[0] == q[0]:
        lo, hi = sorted((p[1], q[1]))
        return x0 < p[0] < x1 and lo < y1 and hi > y0
    lo, hi = sorted((p[0], q[0]))
    return y0 < p[1] < y1 and lo < x1 and hi > x0


def _collisions(points, nodes, skip) -> int:
    hits = 0
    for n in nodes:
        if n.id in skip:
            continue
        r = _rect(n, 6)
        hits += any(_seg_hits(p, q, r) for p, q in zip(points, points[1:]))
    return hits


def _rects_overlap(a, b) -> bool:
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


# ---------------------------------------------------------------- layout


def auto_place(nodes: dict[str, N], edges: list[E], direction: str) -> None:
    """Place nodes that have no {"col","row"}.
    None placed → rank = longest path from a source (cycles broken), order by input,
    one barycentre pass. Some placed → each unplaced node slots in beside a placed
    neighbour (after its source, or before its target), never moving authored nodes."""
    todo = [n for n in nodes.values() if 'col' not in n.data and 'row' not in n.data]
    if not todo:
        return
    if len(todo) < len(nodes):
        _slot_beside(nodes, edges, todo, direction)
        return
    succ: dict[str, list[str]] = {k: [] for k in nodes}
    for e in edges:
        if e.a in nodes and e.b in nodes and e.a != e.b:
            succ[e.a].append(e.b)
    rank: dict[str, int] = {}
    onstack: set = set()

    def dfs(u, d):
        if u in onstack or rank.get(u, -1) >= d:
            return
        rank[u] = d
        onstack.add(u)
        for v in succ[u]:
            dfs(v, d + 1)
        onstack.discard(u)

    indeg = {k: 0 for k in nodes}
    for e in edges:
        if e.b in indeg and e.a != e.b:
            indeg[e.b] += 1
    for k in nodes:
        if indeg[k] == 0:
            dfs(k, 0)
    for k in nodes:
        if k not in rank:
            dfs(k, 0)
    layers: dict[int, list[str]] = {}
    for k in nodes:
        layers.setdefault(rank[k], []).append(k)
    pos = {k: i for L in layers.values() for i, k in enumerate(L)}
    pred: dict[str, list[str]] = {k: [] for k in nodes}
    for u, vs in succ.items():
        for v in vs:
            pred[v].append(u)
    for r in sorted(layers)[1:]:
        L = layers[r]
        L.sort(key=lambda k: (sum(pos[p] for p in pred[k]) / len(pred[k])) if pred[k] else pos[k])
        for i, k in enumerate(L):
            pos[k] = i
    for r, L in layers.items():
        for i, k in enumerate(L):
            n = nodes[k]
            n.col, n.row = (r, i) if direction == 'LR' else (i, r)


def _slot_beside(nodes, edges, todo, direction):
    taken = {(n.col, n.row) for n in nodes.values() if n not in todo}
    main, cross = ('col', 'row') if direction == 'LR' else ('row', 'col')
    for u in todo:
        spot = None
        for e in edges:
            if e.b == u.id and nodes[e.a] not in todo:
                v = nodes[e.a]; spot = [v.col, v.row]; spot[0 if main == 'col' else 1] += 1; break
            if e.a == u.id and nodes[e.b] not in todo:
                v = nodes[e.b]; spot = [v.col, v.row]; spot[0 if main == 'col' else 1] -= 1; break
        if spot is None:
            spot = [0, max((n.row for n in nodes.values() if n not in todo), default=-1) + 1]
        i = 1 if main == 'col' else 0
        while tuple(spot) in taken:
            spot[i] += 1
        u.col, u.row = spot
        taken.add(tuple(spot))
    lo_c = min(n.col for n in nodes.values())
    lo_r = min(n.row for n in nodes.values())
    for n in nodes.values():
        n.col -= lo_c
        n.row -= lo_r


def label_gap(edges: list, base: tuple[int, int], z: bool = True) -> tuple[int, int]:
    """Room for the widest edge label between columns (labels sit on open canvas).
    z: a Z-route splits the gap in two, so a label needs its own half plus clearance."""
    w = max([text_width(e.label.upper(), 8, True) * 1.06 + 8 for e in edges if e.label] or [0])
    need = (2 * (w + 24) if z else w + 48) if w else 0
    return (max(base[0], min(snap_up(need, 8), 360)), base[1])


def grid_place(nodes: dict[str, N], direction: str, gap: tuple[int, int], margin: int = 40, top: int = 40) -> tuple[int, int]:
    """Cell sizes from the largest node per column/row; nodes centred in their cell."""
    cols = sorted({n.col for n in nodes.values()})
    rows = sorted({n.row for n in nodes.values()})
    cw = {c: max(n.w for n in nodes.values() if n.col == c) for c in cols}
    rh = {r: max(n.h for n in nodes.values() if n.row == r) for r in rows}
    cx, x = {}, margin
    for c in range(min(cols), max(cols) + 1):
        w = cw.get(c, 80)
        cx[c] = x + w / 2
        x += w + gap[0]
    cy, y = {}, top
    for r in range(min(rows), max(rows) + 1):
        h = rh.get(r, 40)
        cy[r] = y + h / 2
        y += h + gap[1]
    for n in nodes.values():                       # snap centres so a column shares one x
        n.x = snap(cx[n.col]) - n.w / 2
        n.y = snap(cy[n.row]) - n.h / 2
    width = x - gap[0] + margin
    height = y - gap[1]
    return snap_up(width), snap_up(height)


# ---------------------------------------------------------------- routing


def choose_routes(nodes: dict[str, N], edges: list[E], direction: str) -> None:
    pref = ['HVH', 'HV', 'VH', 'VHV'] if direction == 'LR' else ['VHV', 'VH', 'HV', 'HVH']
    for e in edges:
        A, B = nodes[e.a], nodes[e.b]
        if e.sa and e.sb:                        # forced by the type
            e.route = e.route or ('H' if e.sa in 'lr' and e.sb in 'lr' else 'V' if e.sa in 'tb' and e.sb in 'tb' else 'HV' if e.sa in 'lr' else 'VH')
            continue
        ay0, ay1, by0, by1 = A.y, A.y + A.h, B.y, B.y + B.h
        ax0, ax1, bx0, bx1 = A.x, A.x + A.w, B.x, B.x + B.w
        oy = min(ay1, by1) - max(ay0, by0)
        ox = min(ax1, bx1) - max(ax0, bx0)
        if oy >= 16 and (bx0 >= ax1 or ax0 >= bx1):
            e.route, e.sa = 'H', 'r' if B.cx > A.cx else 'l'
            e.sb = OPP[e.sa]
            continue
        if ox >= 16 and (by0 >= ay1 or ay0 >= by1):
            e.route, e.sa = 'V', 'b' if B.cy > A.cy else 't'
            e.sb = OPP[e.sa]
            continue
        cands = []
        hs = 'r' if B.cx > A.cx else 'l'
        vs = 'b' if B.cy > A.cy else 't'
        for r in pref:
            if r == 'HVH':
                cands.append((r, hs, OPP[hs]))
            elif r == 'VHV':
                cands.append((r, vs, OPP[vs]))
            elif r == 'HV':
                cands.append((r, hs, OPP[vs]))
            else:
                cands.append((r, vs, OPP[hs]))
        best = None
        for r, sa, sb in cands:
            pts = _points(A, B, r, A.side(sa), B.side(sb), None)
            c = _collisions(pts, nodes.values(), {e.a, e.b})
            if best is None or c < best[0]:
                best = (c, r, sa, sb)
            if c == 0:
                break
        _, e.route, e.sa, e.sb = best
        if best[0] > 0 and e.style == 'default':
            e.style = 'transit'                  # rule 5: unavoidable pass-behind is dashed


def fan_attach(nodes: dict[str, N], edges: list[E]) -> None:
    """Rule 4: every connector gets its own attach point, ≥12px apart, ordered so
    neighbours don't cross."""
    ends: dict[tuple[str, str], list[tuple[E, str]]] = {}
    for e in edges:
        ends.setdefault((e.a, e.sa), []).append((e, 'a'))
        ends.setdefault((e.b, e.sb), []).append((e, 'b'))
    for (nid, s), lst in ends.items():
        n = nodes[nid]
        other = lambda item: nodes[item[0].b if item[1] == 'a' else item[0].a]
        lst.sort(key=lambda it: other(it).cy if s in 'lr' else other(it).cx)
        L = n.h if s in 'lr' else n.w
        k = len(lst)
        for i, (e, end) in enumerate(lst):
            if n.shape in ('diamond', 'dot', 'ring') or k == 1:
                t = 0.5
                if k == 1 and e.route in ('H', 'V') and n.shape not in ('diamond', 'dot', 'ring'):
                    o = nodes[e.b if end == 'a' else e.a]
                    if e.route == 'H':
                        lo, hi = max(n.y, o.y), min(n.y + n.h, o.y + o.h)
                        t = ((lo + hi) / 2 - n.y) / n.h
                    else:
                        lo, hi = max(n.x, o.x), min(n.x + n.w, o.x + o.w)
                        t = ((lo + hi) / 2 - n.x) / n.w
            else:
                step = max(12.0, L / (k + 1))
                span = step * (k - 1)
                t = (L / 2 - span / 2 + step * i) / L
            p = n.side(s, t)
            p = (snap(p[0]) if s in 'tb' else p[0], snap(p[1]) if s in 'lr' else p[1])
            if end == 'a':
                e.pa = p
            else:
                e.pb = p
    # straight edges: an end that is alone on its side moves to meet its partner,
    # so the connector stays straight instead of jogging (stays within the side)
    for e in edges:
        if e.route not in ('H', 'V'):
            continue
        A, B = nodes[e.a], nodes[e.b]
        alone_a = len(ends[(e.a, e.sa)]) == 1 and A.shape in ('box', 'pill', 'record')
        alone_b = len(ends[(e.b, e.sb)]) == 1 and B.shape in ('box', 'pill', 'record')
        i = 1 if e.route == 'H' else 0
        lo = lambda n: (n.y if i else n.x) + 8
        hi = lambda n: (n.y + n.h if i else n.x + n.w) - 8
        if e.pa[i] != e.pb[i]:
            if alone_b and lo(B) <= e.pa[i] <= hi(B):
                e.pb = (e.pb[0], e.pa[1]) if i else (e.pa[0], e.pb[1])
            elif alone_a and lo(A) <= e.pb[i] <= hi(A):
                e.pa = (e.pa[0], e.pb[1]) if i else (e.pb[0], e.pa[1])


def _points(A: N, B: N, route: str, pa, pb, channel):
    if route == 'H' or route == 'V':
        if route == 'H' and pa[1] != pb[1]:
            mx = channel if channel is not None else (pa[0] + pb[0]) / 2
            return [pa, (mx, pa[1]), (mx, pb[1]), pb]
        if route == 'V' and pa[0] != pb[0]:
            my = channel if channel is not None else (pa[1] + pb[1]) / 2
            return [pa, (pa[0], my), (pb[0], my), pb]
        return [pa, pb]
    if route == 'HV':
        return [pa, (pb[0], pa[1]), pb]
    if route == 'VH':
        return [pa, (pa[0], pb[1]), pb]
    if route == 'HVH':
        mx = channel if channel is not None else (pa[0] + pb[0]) / 2
        return [pa, (mx, pa[1]), (mx, pb[1]), pb]
    my = channel if channel is not None else (pa[1] + pb[1]) / 2
    return [pa, (pa[0], my), (pb[0], my), pb]


def slot_channels(nodes: dict[str, N], edges: list[E]) -> None:
    """Rule 3: Z-routes sharing a channel run ≥12px apart."""
    groups: dict[tuple, list[E]] = {}
    for e in edges:
        if e.route in ('HVH', 'VHV') or (e.route == 'H' and e.pa[1] != e.pb[1]) or (e.route == 'V' and e.pa[0] != e.pb[0]):
            vertical = e.route in ('HVH', 'H')
            mid = (e.pa[0] + e.pb[0]) / 2 if vertical else (e.pa[1] + e.pb[1]) / 2
            groups.setdefault(('v' if vertical else 'h', snap(mid, 16)), []).append(e)
    for (axis, mid), lst in groups.items():
        k = len(lst)
        lst.sort(key=lambda e: (e.pa[1] if axis == 'v' else e.pa[0]))
        for i, e in enumerate(lst):
            e.channel = snap(mid + (i - (k - 1) / 2) * 12)


def build_points(nodes, edges):
    for e in edges:
        e.points = _points(nodes[e.a], nodes[e.b], e.route, e.pa, e.pb, e.channel)


def place_labels(svg: Svg, nodes: dict[str, N], edges: list[E], placed: list | None = None) -> None:
    """Rule 2 + 6: masked label on an open-canvas segment, clear of nodes and other labels."""
    placed = placed if placed is not None else []
    node_rects = [_rect(n, 4) for n in nodes.values()]
    for e in edges:
        if not e.label:
            continue
        s = e.label.upper()
        w = snap_up(text_width(s, 8, True) + 8)
        segs = sorted(zip(e.points, e.points[1:]), key=lambda pq: -(abs(pq[1][0] - pq[0][0]) + abs(pq[1][1] - pq[0][1])))
        # the architecture grammar puts a Z-route's label on its middle (vertical) segment
        if e.route in ('HVH', 'VHV') and len(e.points) == 4:
            mid = (e.points[1], e.points[2])
            segs = [mid] + [sg for sg in segs if sg != mid]
        choice = None
        for p, q in segs:
            vertical = p[0] == q[0]
            length = abs(q[1] - p[1]) if vertical else abs(q[0] - p[0])
            for frac in (0.5, 0.3, 0.7):
                x = p[0] + (q[0] - p[0]) * frac
                y = p[1] + (q[1] - p[1]) * frac
                opts = ([('right', (x + 10, y - 7, x + 10 + w, y + 5)), ('left', (x - 10 - w, y - 7, x - 10, y + 5))] if vertical
                        else [('above', (x - w / 2, y - 18, x + w / 2, y - 6)), ('below', (x - w / 2, y + 8, x + w / 2, y + 20))])
                for side, r in opts:
                    if length < (24 if vertical else w + 16):
                        continue
                    if any(_rects_overlap(r, nr) for nr in node_rects) or any(_rects_overlap(r, pr) for pr in placed):
                        continue
                    choice = (side, (x, y), r)
                    break
                if choice:
                    break
            if choice:
                break
        if not choice:                       # fall back: longest segment, above/right
            p, q = segs[0]
            x, y = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
            side = 'right' if p[0] == q[0] else 'above'
            choice = (side, (x, y), (x - w / 2, y - 18, x + w / 2, y - 6))
        side, (x, y), r = choice
        placed.append(r)
        if side == 'above':
            svg.label(x, y - 10, e.label)
        elif side == 'below':
            svg.label(x, y + 18, e.label)
        elif side == 'right':
            svg.label(x + 10, y + 3, e.label, anchor='start')
        else:
            svg.label(x - 10, y + 3, e.label, anchor='end')


def route_all(nodes, edges, direction):
    choose_routes(nodes, edges, direction)
    fan_attach(nodes, edges)
    slot_channels(nodes, edges)
    build_points(nodes, edges)


def draw_edges(svg: Svg, edges: list[E], nodes: dict[str, N]) -> None:
    for e in edges:
        draw_edge(svg, e.points, style=e.style, label=None)
    place_labels(svg, nodes, edges)


# ---------------------------------------------------------------- shared spec handling


def _nodes_from(spec, sizer) -> dict[str, N]:
    nodes = {}
    for d in spec['nodes']:
        if 'id' not in d:
            raise SpecError(f"every node needs an id (got {d})")
        w, h, shape = sizer(d)
        n = N(d['id'], w, h, shape=shape, data=d)
        if 'col' in d or 'row' in d:
            n.col, n.row = int(d.get('col', 0)), int(d.get('row', 0))
        nodes[n.id] = n
    return nodes


def _edges_from(spec, nodes, key='edges') -> list[E]:
    edges = []
    for d in spec.get(key, []):
        for k in ('from', 'to'):
            if d.get(k) not in nodes:
                raise SpecError(f"edge {d.get('from')}→{d.get('to')}: '{d.get(k)}' is not a node id")
        edges.append(E(d['from'], d['to'], d.get('style', 'default'), d.get('label'), d))
    return edges


def _check_accent(nodes, edges, limit=2):
    n = sum(1 for x in nodes.values() if x.data.get('kind') in ('focal', 'new')) + sum(1 for e in edges if e.style == 'accent')
    budget('accent elements (focal nodes + accent edges)', n, limit, 'keep 1–2: the one thing the reader must see')


def _std_box(d, tag_key='tag'):
    name, sub, tag = d.get('name', d['id']), d.get('sub'), d.get(tag_key)
    w = fit_width((name, 12, False, 600), (sub, 9, True), minimum=int(d.get('w', 120)))
    h = int(d.get('h', (64 if tag else 56) if sub else (52 if tag else 44)))
    return w, h


def _zones(svg, spec, nodes, pad_x=24, pad_y=36):
    zs = spec.get('zones', [])
    budget('zones', len(zs), 3, 'merge groupings or split the diagram')
    for z in zs:
        members = [nodes[i] for i in z.get('nodes', []) if i in nodes]
        if not members:
            raise SpecError(f"zone '{z.get('label')}' has no known nodes")
        x0 = min(m.x for m in members) - pad_x
        y0 = min(m.y for m in members) - pad_y
        x1 = max(m.x + m.w for m in members) + pad_x
        y1 = max(m.y + m.h for m in members) + 24
        zone(svg, x0, y0, x1 - x0, y1 - y0, z.get('label', ''), dashed=z.get('dashed', False))


def _finish(svg: Svg, nodes, width, height, extra_bottom=0):
    right = max(n.x + n.w for n in nodes.values()) + 40
    bottom = max(n.y + n.h for n in nodes.values())
    svg.width = snap_up(max(width, right, 480))
    legend_y = snap_up(bottom + 48 + extra_bottom)
    svg.height = legend_y + 40
    return svg, legend_y


def _shift_for_zones(spec, nodes, dy=16):
    """Zones need headroom above their first row for the label."""
    if spec.get('zones'):
        for n in nodes.values():
            n.y += dy


# ---------------------------------------------------------------- architecture


def render_architecture(spec):
    need(spec, 'nodes')
    direction = spec.get('direction', 'LR')
    budget('nodes', len(spec['nodes']), 9)
    nodes = _nodes_from(spec, lambda d: (*_std_box(d), 'box'))
    edges = _edges_from(spec, nodes)
    budget('arrows', len(edges), 12)
    _check_accent(nodes, edges)
    auto_place(nodes, edges, direction)
    gap = label_gap(edges, tuple(spec.get('gap', (112, 72) if direction == 'LR' else (72, 88))))
    width, height = grid_place(nodes, direction, gap, top=64 if spec.get('zones') else 40)
    svg = Svg()
    route_all(nodes, edges, direction)
    _zones(svg, spec, nodes)
    draw_edges(svg, edges, nodes)
    for n in nodes.values():
        d = n.data
        node_box(svg, n.x, n.y, n.w, n.h, d.get('name', n.id), d.get('sub'), d.get('tag'), d.get('kind', 'default'))
    return _finish(svg, nodes, width, height)


# ---------------------------------------------------------------- flowchart


def render_flowchart(spec):
    need(spec, 'nodes', 'edges')
    direction = spec.get('direction', 'TB')
    budget('nodes', len(spec['nodes']), 9)

    def sizer(d):
        k = d.get('kind', 'step')
        name = d.get('name', d['id'])
        if k in ('start', 'end'):
            return fit_width((name, 12, False, 600), pad=24, minimum=112), 40, 'pill'
        if k == 'decision':
            w = max(128, snap_up(text_width(name, 12, False, 600) * 1.6 + 32, 8))
            return w, max(72, snap_up(w * 0.55)), 'diamond'
        if k == 'merge':
            return 8, 8, 'dot'
        w, h = _std_box(d)
        return w, h, 'box'

    nodes = _nodes_from(spec, sizer)
    edges = _edges_from(spec, nodes)
    budget('arrows', len(edges), 12)
    for e in edges:
        A = nodes[e.a]
        if A.data.get('kind') == 'decision' and not e.label:
            raise SpecError(f"edge {e.a}→{e.b} leaves a decision: give it a label (e.g. YES / NO)")
    decisions = [n for n in nodes.values() if n.shape == 'diamond']
    for dnode in decisions:
        outs = [e for e in edges if e.a == dnode.id]
        budget(f"exits from decision '{dnode.id}'", len(outs), 3, 'nest a second decision')
    _check_accent(nodes, edges)
    auto_place(nodes, edges, direction)
    width, height = grid_place(nodes, direction, label_gap(edges, tuple(spec.get('gap', (96, 64) if direction == 'TB' else (112, 64)))))
    _diamond_ports(nodes, edges, direction)          # needs real positions
    svg = Svg()
    route_all(nodes, edges, direction)
    draw_edges(svg, edges, nodes)
    for n in nodes.values():
        d = n.data
        k = d.get('kind', 'step')
        name = d.get('name', n.id)
        focal = d.get('focal') or k == 'focal'
        fill, stroke = (tint('accent', 0.08), ACCENT) if focal else (PAPER, INK)
        if n.shape == 'pill':
            svg.el('nodes', 'rect', x=n.x, y=n.y, width=n.w, height=n.h, rx=20, fill=PAPER)
            svg.el('nodes', 'rect', x=n.x, y=n.y, width=n.w, height=n.h, rx=20, fill=fill, stroke=stroke, stroke_width=1.2 if focal else 1)
            svg.text('nodes', n.cx, n.cy + 4, name, size=12, weight=600, anchor='middle')
            svg.key('glyph:<rect x="{x}" y="-6" width="22" height="12" rx="6" fill="#ffffff" stroke="#414448" stroke-width="1" transform="translate(0,{y})"/>'.replace('transform="translate(0,{y})"', '').replace('y="-6"', 'y="{y}"'), 'Start / end')
        elif n.shape == 'diamond':
            pts = f'{_n(n.cx)},{_n(n.y)} {_n(n.x + n.w)},{_n(n.cy)} {_n(n.cx)},{_n(n.y + n.h)} {_n(n.x)},{_n(n.cy)}'
            svg.el('nodes', 'polygon', points=pts, fill=PAPER)
            svg.el('nodes', 'polygon', points=pts, fill=fill, stroke=stroke, stroke_width=1.2 if focal else 1)
            lines = _wrap(name, n.w * 0.62, 12)
            for i, ln in enumerate(lines):
                svg.text('nodes', n.cx, n.cy + 4 + (i - (len(lines) - 1) / 2) * 14, ln, size=12, weight=600, anchor='middle')
            svg.key('glyph:<polygon points="{x},0 0,0" fill="none"/>', 'Decision')
        elif n.shape == 'dot':
            svg.el('nodes', 'circle', cx=n.cx, cy=n.cy, r=4, fill=INK)
        else:
            node_box(svg, n.x, n.y, n.w, n.h, name, d.get('sub'), d.get('tag'), 'focal' if focal else 'default', legend=False)
            svg.key('node:default', 'Step')
    # proper legend glyphs for the flowchart shapes
    svg.legend = [(k, l) for k, l in svg.legend if not k.startswith('glyph:')]
    if any(n.shape == 'pill' for n in nodes.values()):
        svg.legend.insert(0, ('pill', 'Start / end'))
    if decisions:
        svg.legend.append(('diamond', 'Decision'))
    svg.legend = [(_legend_glyph(k), l) for k, l in svg.legend]
    return _finish(svg, nodes, width, height)


def _diamond_ports(nodes, edges, direction):
    """A diamond has four vertices; give every connector its own. Entry on the vertex
    facing upstream, exits spread over the rest, each toward its target."""
    for d in [n for n in nodes.values() if n.shape == 'diamond']:
        entry = 't' if direction == 'TB' else 'l'
        free = [v for v in 'tblr' if v != entry]
        for e in [e for e in edges if e.b == d.id]:
            e.sb = entry
        outs = [e for e in edges if e.a == d.id]
        def pref(e):
            T = nodes[e.b]
            dx, dy = T.cx - d.cx, T.cy - d.cy
            order = []
            if abs(dx) <= 8:
                order = ['b' if dy > 0 else 't']
            order += (['r'] if dx > 0 else ['l']) + (['b'] if dy > 0 else ['t']) + ['r', 'l', 'b', 't']
            return order
        outs.sort(key=lambda e: (0 if abs(nodes[e.b].cx - d.cx) <= 8 else 1))   # straight-down first
        for e in outs:
            v = next((v for v in pref(e) if v in free), None)
            if v is None:
                raise SpecError(f"decision '{d.id}' has more exits than free vertices")
            free.remove(v)
            e.sa = v
            T = nodes[e.b]
            if v in 'lr':
                same_row = abs(T.cy - d.cy) <= 8
                e.sb = OPP[v] if same_row else ('t' if T.cy > d.cy else 'b')
                e.route = 'H' if same_row else 'HV'
            else:
                same_col = abs(T.cx - d.cx) <= 8
                e.sb = OPP[v] if same_col else ('l' if T.cx > d.cx else 'r')
                e.route = 'V' if same_col else 'VH'


def _legend_glyph(kind):
    if kind == 'pill':
        return f'glyph:<rect x="{{x}}" y="{{y}}" width="22" height="12" rx="6" fill="{PAPER}" stroke="{INK}" stroke-width="1" transform="translate(0,-6)"/>'
    if kind == 'diamond':
        return f'glyph:<polygon points="0,0 8,-6 16,0 8,6" fill="{PAPER}" stroke="{INK}" stroke-width="1" transform="translate({{x}},{{y}}) translate(2,0)"/>'
    return kind


def _wrap(s: str, width: float, size: float) -> list[str]:
    words, lines, cur = s.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if text_width(t, size, False, 600) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


# ---------------------------------------------------------------- dependency


def render_dependency(spec):
    need(spec, 'nodes', 'edges')
    budget('nodes', len(spec['nodes']), 9, "collapse leaves into an aggregate '+N leaves' node")
    nodes = _nodes_from(spec, lambda d: (160, 56, 'box'))
    edges = _edges_from(spec, nodes)
    budget('edges', len(edges), 14)
    cyc = spec.get('cycle')
    for n in nodes.values():
        if 'rank' in n.data:
            n.data.setdefault('row', n.data['rank'])
    auto_place(nodes, [e for e in edges if not (cyc and e.a == cyc.get('from') and e.b == cyc.get('to'))], 'TB')
    for n in nodes.values():
        if 'rank' in n.data:
            n.row = int(n.data['rank'])
    budget('rank layers', len({n.row for n in nodes.values()}), 4)
    # re-index columns per rank so each rank is centred
    ranks: dict[int, list[N]] = {}
    for n in nodes.values():
        ranks.setdefault(n.row, []).append(n)
    widest = max(len(v) for v in ranks.values())
    for r, lst in ranks.items():
        lst.sort(key=lambda n: n.col)
        off = (widest - len(lst)) / 2
        for i, n in enumerate(lst):
            n.col = i
            n.data['_off'] = off
    width, height = grid_place(nodes, 'TB', (48, 64))
    for n in nodes.values():
        n.x = snap(n.x + n.data['_off'] * (160 + 48))
    fwd = [e for e in edges if not (cyc and e.a == cyc.get('from') and e.b == cyc.get('to'))]
    for e in fwd:
        if nodes[e.b].row < nodes[e.a].row:
            raise SpecError(f"edge {e.a}→{e.b} points up a rank — dependencies point down; mark it as the 'cycle' if that's the story")
    svg = Svg()
    route_all(nodes, fwd, 'TB')
    draw_edges(svg, fwd, nodes)
    right = max(n.x + n.w for n in nodes.values())
    if cyc:
        A, B = nodes[cyc['from']], nodes[cyc['to']]
        x = right + 32
        pts = [(A.x + A.w, A.cy + 8), (x, A.cy + 8), (x, B.cy - 8), (B.x + B.w, B.cy - 8)]
        draw_edge(svg, pts, style='accent', legend=False)
        svg.layers['edges'][-1] = svg.layers['edges'][-1].replace('<path ', '<path stroke-dasharray="5,4" ', 1)
        svg.label(x + 8, (A.cy + B.cy) / 2 + 3, 'CYCLE', anchor='start', fill=ACCENT)
        svg.legend.append((f'glyph:<path d="M {{x}} {{y}} h 22" stroke="{ACCENT}" stroke-width="1.4" stroke-dasharray="5,4" marker-end="url(#arrow-accent)"/>', 'Cycle'))
        svg.markers.add('arrow-accent')
    fan_in = {k: 0 for k in nodes}
    for e in edges:
        fan_in[e.b] += 1
    kinds = {'internal': 'default', 'external': 'external', 'leaf': 'store', 'focal': 'focal'}
    for n in nodes.values():
        d = n.data
        kind = kinds.get(d.get('kind', 'internal'), d.get('kind', 'default'))
        node_box(svg, n.x, n.y, n.w, n.h, d.get('name', n.id), d.get('sub'), None, kind)
        badge = f'{fan_in[n.id]} in'
        bw = snap_up(text_width(badge, 8, True) + 8)
        svg.el('nodes', 'rect', x=n.x + n.w - bw - 6, y=n.y + 6, width=bw, height=12, rx=2, fill=PAPER, stroke=tint('ink', 0.3), stroke_width=0.8)
        svg.text('nodes', n.x + n.w - 6 - bw / 2, n.y + 15, badge, size=8, mono=True, fill=MUTED, anchor='middle')
    svg.legend = [(k.replace('node:default', 'node:default'), {'node:default': 'Internal', 'node:store': 'Leaf', 'node:external': 'External'}.get(k, l)) for k, l in svg.legend]
    return _finish(svg, nodes, width + 80, height)


# ---------------------------------------------------------------- deployment


def render_deployment(spec):
    need(spec, 'nodes')
    budget('infrastructure nodes', len(spec['nodes']), 6, 'split into one diagram per environment')
    arts = sum(len(d.get('artifacts', [])) for d in spec['nodes'])
    budget('artifact chips', arts, 9)

    def sizer(d):
        name = d.get('name', d['id'])
        chip_w = max([text_width(a.get('name', ''), 12) + text_width(a.get('version', ''), 9, True) + 40 for a in d.get('artifacts', [])] or [0])
        w = fit_width((name, 12, False, 600), minimum=max(160, int(chip_w) + 24))
        h = 52 + len(d.get('artifacts', [])) * 32 + (8 if d.get('artifacts') else 0)
        return w, snap_up(h), 'box'

    nodes = _nodes_from(spec, sizer)
    edges = _edges_from(spec, nodes, 'paths')
    budget('network paths', len(edges), 8)
    zone_of = {i: z.get('label') for z in spec.get('zones', []) for i in z.get('nodes', [])}
    for e in edges:
        if e.style == 'default':
            e.style = 'dashed' if e.data.get('async') else ('accent' if e.data.get('accent') else ('link' if zone_of.get(e.a) != zone_of.get(e.b) else 'default'))
    _check_accent(nodes, edges)
    auto_place(nodes, edges, spec.get('direction', 'LR'))
    width, height = grid_place(nodes, 'LR', label_gap(edges, tuple(spec.get('gap', (112, 72)))), top=72)
    svg = Svg()
    route_all(nodes, edges, spec.get('direction', 'LR'))
    for z in spec.get('zones', []):
        z.setdefault('dashed', True)
    _zones(svg, spec, nodes, pad_y=40)
    draw_edges(svg, edges, nodes)
    for n in nodes.values():
        d = n.data
        kind = 'focal' if d.get('accent') or d.get('kind') == 'focal' else d.get('kind', 'default')
        fill, stroke, dash, lg = NODE_KINDS[kind]
        svg.el('nodes', 'rect', x=n.x, y=n.y, width=n.w, height=n.h, rx=6, fill=PAPER)
        svg.el('nodes', 'rect', x=n.x, y=n.y, width=n.w, height=n.h, rx=6, fill=fill, stroke=stroke, stroke_width=1.2 if kind == 'focal' else 1, stroke_dasharray=dash)
        svg.key(f'node:{kind}', {'default': 'Host / service', 'focal': 'New / single point of failure'}.get(kind, lg))
        tag = (d.get('tag') or 'POD').upper()
        tw = snap_up(text_width(tag, 7, True) + 10)
        svg.el('nodes', 'rect', x=n.x + 8, y=n.y + 6, width=tw, height=12, rx=2, fill='none', stroke=stroke, stroke_opacity=0.4, stroke_width=0.8)
        svg.text('nodes', n.x + 8 + tw / 2, n.y + 15, tag, size=7, mono=True, fill=stroke, anchor='middle', spacing='0.08em')
        if d.get('replicas'):
            rep = f"x{d['replicas']}"
            rw = snap_up(text_width(rep, 8, True) + 8)
            svg.el('nodes', 'rect', x=n.x + n.w - rw - 8, y=n.y + 6, width=rw, height=12, rx=2, fill='none', stroke=tint('ink', 0.3), stroke_width=0.8)
            svg.text('nodes', n.x + n.w - 8 - rw / 2, n.y + 15, rep, size=8, mono=True, fill=MUTED, anchor='middle')
        svg.text('nodes', n.x + 12, n.y + 40, d.get('name', n.id), size=12, weight=600)
        cy = n.y + 52
        for a in d.get('artifacts', []):
            svg.el('nodes', 'rect', x=n.x + 12, y=cy, width=n.w - 24, height=24, rx=4, fill=tint('ink', 0.05), stroke=MUTED, stroke_width=0.8)
            svg.text('nodes', n.x + 20, cy + 16, a.get('name', ''), size=12)
            svg.text('nodes', n.x + n.w - 20, cy + 16, a.get('version', ''), size=9, mono=True, fill=MUTED, anchor='end')
            cy += 32
    if arts:
        svg.key(f'swatch:{tint("ink", 0.05)}|{MUTED}', 'Artifact · version')
    svg.legend = [(k, {'API / external call': 'Crosses a boundary', 'Flow': 'Within a zone'}.get(l, l)) for k, l in svg.legend]
    return _finish(svg, nodes, width, height)


# ---------------------------------------------------------------- tree + org chart


def _tree_layout(spec, sizer, gap_x=24, gap_y=56):
    need(spec, 'nodes')
    items = {d['id']: d for d in spec['nodes']}
    kids: dict[str, list[str]] = {k: [] for k in items}
    roots = []
    for d in spec['nodes']:
        p = d.get('parent')
        if p is None:
            roots.append(d['id'])
        elif p not in items:
            raise SpecError(f"node '{d['id']}' has unknown parent '{p}'")
        else:
            kids[p].append(d['id'])
    if len(roots) != 1:
        raise SpecError(f"a tree needs exactly one root (no parent); found {len(roots)}: {roots}")
    for k, v in kids.items():
        budget(f"children of '{k}'", len(v), 5, 'add a grouping node')
    nodes = {}
    for k, d in items.items():
        w, h = sizer(d)
        nodes[k] = N(k, w, h, data=d)

    def depth(k):
        return 1 + max((depth(c) for c in kids[k]), default=0)

    budget('tree depth', depth(roots[0]), 4)

    def span(k):
        own = nodes[k].w
        if not kids[k]:
            return own
        return max(own, sum(span(c) for c in kids[k]) + gap_x * (len(kids[k]) - 1))

    level_h: dict[int, int] = {}

    def levels(k, lv):
        level_h[lv] = max(level_h.get(lv, 0), nodes[k].h)
        for c in kids[k]:
            levels(c, lv + 1)

    levels(roots[0], 0)
    ys, y = {}, 40
    for lv in sorted(level_h):
        ys[lv] = y
        y += level_h[lv] + gap_y

    def place(k, x0, lv):
        s = span(k)
        n = nodes[k]
        n.x = snap(x0 + s / 2 - n.w / 2)
        n.y = ys[lv]
        cx = x0 + (s - (sum(span(c) for c in kids[k]) + gap_x * (len(kids[k]) - 1))) / 2
        for c in kids[k]:
            place(c, cx, lv + 1)
            cx += span(c) + gap_x

    place(roots[0], 40, 0)
    return nodes, kids, roots[0]


def _bus(svg, nodes, kids):
    """Parent drop → horizontal sibling bus → child drops, 1px muted, r=8 corners."""
    for p, cs in kids.items():
        if not cs:
            continue
        P = nodes[p]
        top = min(nodes[c].y for c in cs)
        by = snap(P.y + P.h + (top - P.y - P.h) / 2)
        svg.el('edges', 'line', x1=P.cx, y1=P.y + P.h, x2=P.cx, y2=by, stroke=MUTED, stroke_width=1)
        for c in cs:
            C = nodes[c]
            svg.el('edges', 'path', d=ortho_path([(P.cx, by), (C.cx, by), (C.cx, C.y)]), fill='none', stroke=MUTED, stroke_width=1)


def render_tree(spec):
    def sizer(d):
        w, h = _std_box(d)
        return w, h
    nodes, kids, root = _tree_layout(spec, sizer)
    budget('focal nodes', sum(1 for n in nodes.values() if n.data.get('kind') == 'focal'), 1, 'one focal: the root or the critical leaf')
    svg = Svg()
    _bus(svg, nodes, kids)
    for k, n in nodes.items():
        d = n.data
        kind = d.get('kind', 'store' if not kids[k] else 'default')
        node_box(svg, n.x, n.y, n.w, n.h, d.get('name', k), d.get('sub'), d.get('tag'), kind)
    svg.legend = [(k, {'Store / state': 'Leaf', 'Component': 'Node'}.get(l, l)) for k, l in svg.legend]
    w = max(n.x + n.w for n in nodes.values()) + 40
    return _finish(svg, nodes, w, 0)


def render_org_chart(spec):
    budget('nodes', len(spec.get('nodes', [])), 12, 'group specialists into pods')

    def sizer(d):
        w = fit_width((d.get('name', d['id']), 12, False, 600), (d.get('invoke'), 9, True), (d.get('scope'), 9), minimum=140)
        return w, 64 if d.get('scope') else 52

    nodes, kids, root = _tree_layout(spec, sizer)
    treat = {'front-door': 'focal', 'team': 'default', 'owner-active': 'default', 'owner-external': 'external',
             'gap': 'optional', 'approval': 'boundary'}
    labels = {'focal': 'Front door', 'default': 'Owner / team', 'external': 'External owner', 'optional': 'Gap (unowned)', 'boundary': 'Approval gate'}
    budget('coral nodes', sum(1 for n in nodes.values() if treat.get(n.data.get('treatment', 'team')) == 'focal' or n.data.get('kind') == 'focal'), 1)
    svg = Svg()
    _bus(svg, nodes, kids)
    for k, n in nodes.items():
        d = n.data
        kind = d.get('kind') or treat.get(d.get('treatment', 'front-door' if k == root else 'team'), 'default')
        fill, stroke, dash, _ = NODE_KINDS[kind]
        svg.el('nodes', 'rect', x=n.x, y=n.y, width=n.w, height=n.h, rx=6, fill=PAPER)
        svg.el('nodes', 'rect', x=n.x, y=n.y, width=n.w, height=n.h, rx=6, fill=fill, stroke=stroke, stroke_width=1.2 if kind == 'focal' else 1, stroke_dasharray=dash)
        svg.key(f'node:{kind}', labels.get(kind, kind))
        svg.text('nodes', n.cx, n.y + 22, d.get('name', k), size=12, weight=600, anchor='middle')
        if d.get('invoke'):
            svg.text('nodes', n.cx, n.y + 38, d['invoke'], size=9, mono=True, fill=MUTED, anchor='middle')
        if d.get('scope'):
            svg.text('nodes', n.cx, n.y + 53, d['scope'], size=9, fill=SOFT, anchor='middle')
    w = max(n.x + n.w for n in nodes.values()) + 40
    return _finish(svg, nodes, w, 0)


# ---------------------------------------------------------------- state machine


def _cubic_mid(p0, p1, p2, p3, t=0.5):
    u = 1 - t
    return (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])


def render_state(spec):
    need(spec, 'states', 'transitions')
    direction = spec.get('direction', 'LR')
    items = list(spec['states'])
    if spec.get('initial'):
        items.insert(0, {'id': '__initial', 'kind': 'initial', **({k: spec['initial_pos'][k] for k in ('col', 'row')} if spec.get('initial_pos') else {})})
    if spec.get('final'):
        finals = spec['final'] if isinstance(spec['final'], list) else [spec['final']]
        for i, f in enumerate(finals):
            items.append({'id': f'__final{i}', 'kind': 'final', '_of': f})
    spec2 = {'nodes': items}

    def sizer(d):
        if d.get('kind') == 'initial':
            return 12, 12, 'dot'
        if d.get('kind') == 'final':
            return 16, 16, 'ring'
        w = fit_width((d.get('name', d['id']), 12, False, 600), (d.get('sub'), 9, True), minimum=112)
        return w, 48 if not d.get('sub') else 56, 'box'

    nodes = _nodes_from(spec2, sizer)
    trans = []
    if spec.get('initial'):
        trans.append({'from': '__initial', 'to': spec['initial']})
    for d in spec['transitions']:
        trans.append(d)
    if spec.get('final'):
        finals = spec['final'] if isinstance(spec['final'], list) else [spec['final']]
        for i, f in enumerate(finals):
            trans.append({'from': f, 'to': f'__final{i}'})
    for d in trans:
        for k in ('from', 'to'):
            if d[k] not in nodes:
                raise SpecError(f"transition {d['from']}→{d['to']}: '{d[k]}' is not a state id")
    real = [s for s in spec['states']]
    budget('transitions', len(spec['transitions']), max(2 * len(real), 1), 'this is probably two machines')
    budget('focal states', sum(1 for s in real if s.get('focal') or s.get('kind') == 'focal'), 1, 'one: the error state or the happy completion')
    edges = [E(d['from'], d['to'], 'accent' if d.get('accent') else 'default', _trans_label(d), d) for d in trans]
    auto_place(nodes, [e for e in edges if e.a != e.b], direction)
    width, height = grid_place(nodes, direction, tuple(spec.get('gap', (120, 88))), top=72)
    svg = Svg()
    pairs = {(e.a, e.b) for e in edges}
    placed_labels = []
    for e in edges:
        A, B = nodes[e.a], nodes[e.b]
        stroke, sw, mk = (ACCENT, 1.4, 'arrow-accent') if e.style == 'accent' else (MUTED, 1.2, 'arrow')
        if e.a == e.b:                                  # self-loop above the state
            x0, x1, y = A.cx - 16, A.cx + 16, A.y
            d = f'M {_n(x0)} {_n(y)} C {_n(x0 - 8)} {_n(y - 44)} {_n(x1 + 8)} {_n(y - 44)} {_n(x1)} {_n(y)}'
            svg.el('edges', 'path', d=d, fill='none', stroke=stroke, stroke_width=sw, marker_end=svg.marker(mk))
            if e.label:
                r = svg.label(A.cx, y - 40, e.label, upper=False, size=9)
                placed_labels.append((r[0], r[1], r[0] + r[2], r[1] + r[3]))
            continue
        horizontal = abs(B.cx - A.cx) >= abs(B.cy - A.cy)
        if horizontal:
            sa, sb = ('r', 'l') if B.cx > A.cx else ('l', 'r')
        else:
            sa, sb = ('b', 't') if B.cy > A.cy else ('t', 'b')
        bend = 0
        if (e.b, e.a) in pairs:                          # two-way pair: bow apart
            bend = -28 if (e.a < e.b) else 28
        elif horizontal and B.cx < A.cx:                 # back edge: arc under the row
            sa, sb, bend = 'b', 'b', 0
        p0, p3 = A.side(sa), B.side(sb)
        if sa == 'b' and sb == 'b':
            dip = max(A.y + A.h, B.y + B.h) + 56
            p1, p2 = (p0[0], dip), (p3[0], dip)
        else:
            k = max(40, math.hypot(p3[0] - p0[0], p3[1] - p0[1]) / 3)
            nx = {'r': (1, 0), 'l': (-1, 0), 'b': (0, 1), 't': (0, -1)}
            p1 = (p0[0] + nx[sa][0] * k, p0[1] + nx[sa][1] * k + (bend if horizontal else 0))
            p2 = (p3[0] + nx[sb][0] * k, p3[1] + nx[sb][1] * k + (bend if horizontal else 0))
            if not horizontal:
                p1 = (p1[0] + bend, p1[1])
                p2 = (p2[0] + bend, p2[1])
        d = f'M {_n(p0[0])} {_n(p0[1])} C {_n(p1[0])} {_n(p1[1])} {_n(p2[0])} {_n(p2[1])} {_n(p3[0])} {_n(p3[1])}'
        svg.el('edges', 'path', d=d, fill='none', stroke=stroke, stroke_width=sw, marker_end=svg.marker(mk))
        if e.label:
            mx, my = _cubic_mid(p0, p1, p2, p3)
            ax, ay = _cubic_mid(p0, p1, p2, p3, 0.45)
            bx, by = _cubic_mid(p0, p1, p2, p3, 0.55)
            steep = abs(by - ay) > abs(bx - ax)
            if sa == 'b' and sb == 'b':
                r = svg.label(mx, my + 18, e.label, upper=False, size=9)
            elif steep:
                r = svg.label(mx + 10, my + 3, e.label, anchor='start', upper=False, size=9)
            else:
                r = svg.label(mx, my - 10 if bend <= 0 else my + 18, e.label, upper=False, size=9)
            placed_labels.append((r[0], r[1], r[0] + r[2], r[1] + r[3]))
    for n in nodes.values():
        d = n.data
        if n.shape == 'dot':
            svg.el('nodes', 'circle', cx=n.cx, cy=n.cy, r=6, fill=INK)
            continue
        if n.shape == 'ring':
            svg.el('nodes', 'circle', cx=n.cx, cy=n.cy, r=8, fill=PAPER, stroke=INK, stroke_width=1.2)
            svg.el('nodes', 'circle', cx=n.cx, cy=n.cy, r=5, fill=INK)
            continue
        kind = 'focal' if d.get('focal') or d.get('kind') == 'focal' else d.get('kind', 'default')
        node_box(svg, n.x, n.y, n.w, n.h, d.get('name', n.id), d.get('sub'), None, kind, rx=8, legend=False)
        svg.key(f'node:{kind}', {'default': 'State', 'focal': 'Focal state'}.get(kind, NODE_KINDS[kind][3]))
    svg.legend.insert(0, (f'glyph:<circle cx="{{x}}" cy="{{y}}" r="5" fill="{INK}" transform="translate(8,0)"/>', 'Initial'))
    if spec.get('final'):
        svg.legend.insert(1, (f'glyph:<g transform="translate(8,0)"><circle cx="{{x}}" cy="{{y}}" r="6" fill="{PAPER}" stroke="{INK}" stroke-width="1.2"/><circle cx="{{x}}" cy="{{y}}" r="3.5" fill="{INK}"/></g>', 'Final'))
    svg.legend.append((f'glyph:<path d="M {{x}} {{y}} q 11 -8 22 0" fill="none" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#arrow)"/>', 'event [guard] / action'))
    svg.markers.add('arrow')
    return _finish(svg, nodes, width, height, extra_bottom=40)


def _trans_label(d):
    parts = []
    if d.get('event'):
        parts.append(d['event'])
    if d.get('guard'):
        parts.append(f"[{d['guard'].strip('[]')}]")
    s = ' '.join(parts)
    if d.get('action'):
        s = f"{s} / {d['action']}" if s else f"/ {d['action']}"
    return s or d.get('label')


# ---------------------------------------------------------------- records: er, db-schema, uml-class


def _record_nodes(spec, key, sizer):
    items = spec[key]
    return {d['id'] if 'id' in d else d['name']: N(d.get('id', d['name']), *sizer(d), shape='record', data=d) for d in items}


def _place_records(spec, nodes, edges, direction='LR', gap=(112, 64)):
    for n in nodes.values():
        if 'col' in n.data or 'row' in n.data:
            n.col, n.row = int(n.data.get('col', 0)), int(n.data.get('row', 0))
    auto_place(nodes, edges, direction)
    return grid_place(nodes, direction, gap, top=48)


def render_er(spec):
    need(spec, 'entities')

    def sizer(d):
        rows = [('# ' if f.get('pk') else '→ ' if f.get('fk') else '  ') + f['name'] for f in d.get('fields', [])]
        w = fit_width((d['name'], 12, False, 600), *[(r, 9, True) for r in rows], minimum=max(144, int(text_width(d['name'], 12, False, 600) + 76)))
        return w, 32 + 20 * len(rows) + 8

    nodes = _record_nodes(spec, 'entities', sizer)
    rels = []
    for r in spec.get('relationships', []):
        for k in ('from', 'to'):
            if r[k] not in nodes:
                raise SpecError(f"relationship {r['from']}–{r['to']}: '{r[k]}' is not an entity")
        rels.append(E(r['from'], r['to'], 'plain', r.get('label'), r))
    width, height = _place_records(spec, nodes, rels)
    svg = Svg()
    route_all(nodes, rels, 'LR')
    placed = []
    for e in rels:
        draw_edge(svg, e.points, style='plain', legend=False)
        for end, p, s in (('card_from', e.pa, e.sa), ('card_to', e.pb, e.sb)):
            c = e.data.get(end)
            if not c:
                continue
            ox, oy = {'r': (14, -6), 'l': (-14, -6), 't': (10, -12), 'b': (10, 18)}[s]
            anchor = 'start' if s in 'rtb' else 'end'
            if s in 'lr':
                anchor = 'start' if s == 'r' else 'end'
            r = svg.label(p[0] + ox, p[1] + oy, c, anchor=anchor, upper=False)
            placed.append((r[0], r[1], r[0] + r[2], r[1] + r[3]))
    place_labels(svg, nodes, [e for e in rels if e.label], placed)
    focal_seen = 0
    for n in nodes.values():
        d = n.data
        focal = bool(d.get('focal'))
        focal_seen += focal
        stroke = ACCENT if focal else INK
        svg.el('nodes', 'rect', x=n.x, y=n.y, width=n.w, height=n.h, rx=6, fill=PAPER, stroke=stroke, stroke_width=1.2 if focal else 1)
        svg.el('nodes', 'rect', x=n.x + 0.5, y=n.y + 0.5, width=n.w - 1, height=31.5, rx=6, fill=tint('accent', 0.08) if focal else tint('ink', 0.03))
        svg.el('nodes', 'line', x1=n.x, y1=n.y + 32, x2=n.x + n.w, y2=n.y + 32, stroke=stroke, stroke_opacity=0.35, stroke_width=0.8)
        svg.text('nodes', n.x + 12, n.y + 21, d['name'], size=12, weight=600)
        tag = 'ENTITY'
        tw = snap_up(text_width(tag, 7, True) + 10)
        svg.el('nodes', 'rect', x=n.x + n.w - tw - 8, y=n.y + 10, width=tw, height=12, rx=2, fill='none', stroke=stroke, stroke_opacity=0.4, stroke_width=0.8)
        svg.text('nodes', n.x + n.w - 8 - tw / 2, n.y + 19, tag, size=7, mono=True, fill=stroke, anchor='middle', spacing='0.08em')
        for i, f in enumerate(d.get('fields', [])):
            mark = '# ' if f.get('pk') else '→ ' if f.get('fk') else '  '
            svg.text('nodes', n.x + 12, n.y + 32 + 20 * i + 18, mark + f['name'], size=9, mono=True, fill=INK if f.get('pk') else MUTED)
    budget('focal entities', focal_seen, 1, 'accent the aggregate root only')
    svg.key(f'swatch:{tint("ink", 0.03)}|{INK}', 'Entity')
    if focal_seen:
        svg.key(f'swatch:{tint("accent", 0.08)}|{ACCENT}', 'Aggregate root')
    svg.key(f'glyph:<text x="{{x}}" y="{{y}}" dy="3" font-size="9" font-family="\'Geist Mono\', monospace" fill="{INK}"># id</text>', 'Primary key')
    svg.key(f'glyph:<text x="{{x}}" y="{{y}}" dy="3" font-size="9" font-family="\'Geist Mono\', monospace" fill="{MUTED}">→ fk</text>', 'Foreign key')
    svg.key(f'glyph:<text x="{{x}}" y="{{y}}" dy="3" font-size="9" font-family="\'Geist Mono\', monospace" fill="{SOFT}">1 · N</text>', 'Cardinality')
    return _finish(svg, nodes, width, height)


CHIP_ORDER = ('PK', 'FK', 'UQ', 'NN')


def render_db_schema(spec):
    need(spec, 'tables')
    budget('tables', len(spec['tables']), 5, 'show the subsystem and say so in a caption')

    def cols_shown(d):
        cols = d.get('columns', [])
        budget(f"columns shown in {d['name']}", len(cols), 8, "add 'hidden': N for the rest")
        return cols

    def sizer(d):
        cols = cols_shown(d)
        name_w = max([text_width(c['name'], 12) for c in cols] or [0])
        chip_w = max([sum(text_width(ch, 8, True) + 12 for ch in c.get('chips', [])) for c in cols] or [0])
        type_w = max([text_width(c.get('type', ''), 9, True) for c in cols] or [0])
        w = fit_width((d['name'], 12, False, 600), minimum=int(name_w * 1.08 + chip_w + type_w + 72))
        extra = 24 if d.get('hidden') else 0
        idx = (24 + 16 * len(d['indexes'])) if d.get('indexes') else 0
        return w, 36 + 24 * len(cols) + extra + idx

    nodes = _record_nodes(spec, 'tables', sizer)
    fks = []
    for f in spec.get('fks', []):
        try:
            (ta, ca), (tb, cb) = f['from'].rsplit('.', 1), f['to'].rsplit('.', 1)
        except ValueError:
            raise SpecError(f"fk '{f}': write from/to as table.column")
        for t, c in ((ta, ca), (tb, cb)):
            if t not in nodes:
                raise SpecError(f"fk {f['from']}→{f['to']}: table '{t}' not found")
            if c not in [x['name'] for x in nodes[t].data.get('columns', [])]:
                raise SpecError(f"fk {f['from']}→{f['to']}: column '{c}' not shown in {t} (show it, or drop the fk)")
        action = f.get('on_delete')
        e = E(ta, tb, 'accent' if (action or '').upper() == 'CASCADE' else 'default', f'ON DELETE {action.upper()}' if action else None, {'ca': ca, 'cb': cb})
        fks.append(e)
    budget('FK edges', len(fks), 6)
    budget('CASCADE edges (the one accent)', sum(1 for e in fks if e.style == 'accent'), 1, 'accent only the cascade the story is about')
    width, height = _place_records(spec, nodes, fks, gap=label_gap(fks, (128, 56)))
    svg = Svg()
    # port anchoring: FK edges run row-centre to row-centre on the facing sides
    for e in fks:
        A, B = nodes[e.a], nodes[e.b]
        ia = [c['name'] for c in A.data['columns']].index(e.data['ca'])
        ib = [c['name'] for c in B.data['columns']].index(e.data['cb'])
        ya, yb = A.y + 36 + 24 * ia + 12, B.y + 36 + 24 * ib + 12
        if B.x >= A.x + A.w:
            pa, pb = (A.x + A.w, ya), (B.x, yb)
            mx = (pa[0] + pb[0]) / 2
            pts = [pa, (mx, ya), (mx, yb), pb]
        elif A.x >= B.x + B.w:
            pa, pb = (A.x, ya), (B.x + B.w, yb)
            mx = (pa[0] + pb[0]) / 2
            pts = [pa, (mx, ya), (mx, yb), pb]
        else:                                          # stacked: loop out the right side
            x = max(A.x + A.w, B.x + B.w) + 32
            pts = [(A.x + A.w, ya), (x, ya), (x, yb), (B.x + B.w, yb)]
        e.points, e.route = pts, 'HVH'
        e.pa, e.pb = pts[0], pts[-1]
        draw_edge(svg, pts, style=e.style, legend=False)
    place_labels(svg, nodes, fks)
    cascade_targets = {e.b for e in fks if e.style == 'accent'}
    for n in nodes.values():
        d = n.data
        cols = d['columns']
        focal = n.id in cascade_targets
        svg.el('nodes', 'rect', x=n.x, y=n.y, width=n.w, height=n.h, rx=6, fill=PAPER, stroke=INK, stroke_width=1)
        svg.el('nodes', 'rect', x=n.x + 0.5, y=n.y + 0.5, width=n.w - 1, height=35.5, rx=6, fill=tint('accent', 0.08) if focal else tint('ink', 0.03))
        svg.el('nodes', 'line', x1=n.x, y1=n.y + 36, x2=n.x + n.w, y2=n.y + 36, stroke=tint('ink', 0.2), stroke_width=0.8)
        svg.text('nodes', n.x + 12, n.y + 23, d['name'], size=12, weight=600)
        tw = snap_up(text_width('TABLE', 7, True) + 10)
        svg.el('nodes', 'rect', x=n.x + n.w - tw - 8, y=n.y + 12, width=tw, height=12, rx=2, fill='none', stroke=INK, stroke_opacity=0.4, stroke_width=0.8)
        svg.text('nodes', n.x + n.w - 8 - tw / 2, n.y + 21, 'TABLE', size=7, mono=True, fill=INK, anchor='middle', spacing='0.08em')
        for i, c in enumerate(cols):
            ry = n.y + 36 + 24 * i
            if i % 2 == 1:
                svg.el('nodes', 'rect', x=n.x + 1, y=ry, width=n.w - 2, height=24, fill=tint('ink', 0.02))
            svg.text('nodes', n.x + 12, ry + 16, c['name'], size=12)
            cx = n.x + 12 + max(text_width(x['name'], 12) for x in cols) * 1.08 + 16
            for ch in [x for x in CHIP_ORDER if x in [y.upper() for y in c.get('chips', [])]]:
                cw = snap_up(text_width(ch, 8, True) + 8)
                strong = ch in ('PK', 'FK')
                svg.el('nodes', 'rect', x=_n(cx), y=ry + 6, width=cw, height=12, rx=2, fill='none', stroke=INK if strong else MUTED, stroke_opacity=0.5, stroke_width=0.8)
                svg.text('nodes', cx + cw / 2, ry + 15, ch, size=8, mono=True, fill=INK if strong else MUTED, anchor='middle')
                cx += cw + 4
            svg.text('nodes', n.x + n.w - 12, ry + 16, c.get('type', ''), size=9, mono=True, fill=MUTED, anchor='end')
        y = n.y + 36 + 24 * len(cols)
        if d.get('hidden'):
            svg.text('nodes', n.x + 12, y + 16, f"+ {d['hidden']} more columns", size=9, mono=True, fill=MUTED)
            y += 24
        if d.get('indexes'):
            svg.el('nodes', 'line', x1=n.x, y1=y, x2=n.x + n.w, y2=y, stroke=tint('ink', 0.2), stroke_width=0.8)
            svg.text('nodes', n.x + 12, y + 16, 'INDEXES', size=8, mono=True, fill=MUTED, spacing='0.12em')
            for j, ix in enumerate(d['indexes']):
                svg.text('nodes', n.x + 12, y + 32 + 16 * j, ix, size=9, mono=True, fill=MUTED)
    svg.key(f'swatch:{tint("ink", 0.03)}|{INK}', 'Table')
    if cascade_targets:
        svg.key(f'swatch:{tint("accent", 0.08)}|{INK}', 'Cascades into')
    if any(e.style == 'default' for e in fks):
        svg.key('line:default', 'Foreign key')
    if cascade_targets:
        svg.key('line:accent', 'ON DELETE CASCADE')
    svg.key(f'glyph:<rect x="{{x}}" y="{{y}}" width="20" height="12" rx="2" fill="none" stroke="{INK}" stroke-opacity="0.5" stroke-width="0.8" transform="translate(0,-6)"/>', 'PK · FK · UQ · NN')
    return _finish(svg, nodes, width, height)


UML = {  # kind -> (dash, marker, legend)
    'extends': (None, 'tri-hollow', 'Extends'),
    'implements': ('5,4', 'tri-hollow', 'Implements'),
    'composition': (None, 'dia-filled', 'Composition (owns)'),
    'aggregation': (None, 'dia-hollow', 'Aggregation (has)'),
    'association': (None, 'open-ink', 'Association'),
    'dependency': ('4,3', 'open-ink', 'Depends on'),
}


def render_uml_class(spec):
    need(spec, 'classes')
    budget('classes', len(spec['classes']), 7, 'split by package')

    def sizer(d):
        attrs, ops = d.get('attrs', []), d.get('ops', [])
        for what, lst in (('attributes', attrs), ('operations', ops)):
            budget(f"{what} in {d['name']}", len(lst), 5, "show the ones that matter; end with '…'")
        w = fit_width((d['name'], 12, False, 600), *[(m, 9, True) for m in attrs + ops], minimum=160)
        h = 40 + (d.get('kind') == 'interface') * 12
        h += (12 + 16 * len(attrs)) if attrs else 0
        h += (12 + 16 * len(ops)) if ops else 0
        return w, snap_up(h)

    nodes = _record_nodes(spec, 'classes', sizer)
    rels = []
    for r in spec.get('rels', []):
        for k in ('from', 'to'):
            if r[k] not in nodes:
                raise SpecError(f"rel {r['from']}→{r['to']}: '{r[k]}' is not a class")
        if r.get('kind') not in UML:
            raise SpecError(f"rel kind '{r.get('kind')}' — use one of: {', '.join(UML)}")
        rels.append(E(r['from'], r['to'], 'plain', r.get('label'), r))
    budget('relationships', len(rels), 8)
    width, height = _place_records(spec, nodes, rels, direction=spec.get('direction', 'TB'), gap=(96, 88))
    svg = Svg()
    route_all(nodes, rels, spec.get('direction', 'TB'))
    placed = []
    for e in rels:
        dash, mk, _ = UML[e.data['kind']]
        svg.el('edges', 'path', d=ortho_path(e.points), fill='none', stroke=INK, stroke_width=1, stroke_dasharray=dash, marker_end=svg.marker(mk))
        for end, p, s in (('mult_from', e.pa, e.sa), ('mult_to', e.pb, e.sb)):
            c = e.data.get(end)
            if c:
                ox, oy = {'r': (14, -6), 'l': (-14, -6), 't': (10, -12), 'b': (10, 20)}[s]
                r = svg.label(p[0] + ox, p[1] + oy, c, anchor='end' if s == 'l' else 'start', upper=False)
                placed.append((r[0], r[1], r[0] + r[2], r[1] + r[3]))
    place_labels(svg, nodes, [e for e in rels if e.label], placed)
    focal = 0
    for n in nodes.values():
        d = n.data
        f = bool(d.get('focal'))
        focal += f
        stroke = ACCENT if f else INK
        svg.el('nodes', 'rect', x=n.x, y=n.y, width=n.w, height=n.h, rx=6, fill=tint('accent', 0.08) if f else PAPER, stroke=stroke, stroke_width=1.2 if f else 1)
        y = n.y + 8
        if d.get('kind') == 'interface':
            svg.text('nodes', n.cx, y + 10, '«interface»', size=8, mono=True, fill=MUTED, anchor='middle')
            y += 12
        svg.text('nodes', n.cx, y + 17, d['name'], size=12, weight=600, anchor='middle', italic=d.get('kind') == 'abstract')
        y = n.y + 40 + (d.get('kind') == 'interface') * 12
        for group in ('attrs', 'ops'):
            lst = d.get(group, [])
            if not lst:
                continue
            svg.el('nodes', 'line', x1=n.x, y1=y, x2=n.x + n.w, y2=y, stroke=stroke, stroke_opacity=0.35, stroke_width=0.8)
            for i, m in enumerate(lst):
                svg.text('nodes', n.x + 12, y + 18 + 16 * i, m, size=9, mono=True, fill=INK)
            y += 12 + 16 * len(lst)
    budget('focal classes', focal, 1, 'accent the class being implemented or extended')
    svg.legend = []
    for kind, (dash, mk, lg) in UML.items():            # the doc: legend always shows all six
        da = f' stroke-dasharray="{dash}"' if dash else ''
        svg.legend.append((f'glyph:<path d="M {{x}} {{y}} h 22" stroke="{INK}" stroke-width="1"{da} marker-end="url(#{mk})"/>', lg))
        svg.markers.add(mk)
    return _finish(svg, nodes, width, height, extra_bottom=20)


# ---------------------------------------------------------------- swimlane


def render_swimlane(spec):
    """Lanes are rows (one per owner), steps sit in exactly one lane, columns are order.
    A handoff is an edge that crosses lanes; accent the one with the most coupling."""
    need(spec, 'lanes', 'steps')
    lanes = spec['lanes']
    budget('lanes', len(lanes), 5, 'merge owners or split the process')
    budget('steps', len(spec['steps']), 12)
    lane_ix = {l['id']: i for i, l in enumerate(lanes)}
    items = []
    for i, d in enumerate(spec['steps']):
        if d.get('lane') not in lane_ix:
            raise SpecError(f"step '{d.get('id')}': lane '{d.get('lane')}' is not declared in lanes")
        items.append({**d, 'row': lane_ix[d['lane']], 'col': d.get('col', d.get('order', i))})
    nodes = _nodes_from({'nodes': items}, lambda d: (*_std_box(d), 'box'))
    edges = _edges_from(spec, nodes)
    _check_accent(nodes, edges)
    label_w = snap_up(max(text_width(l.get('label', l['id']).upper(), 8, True) * 1.14 for l in lanes) + 48, 8)
    gap = tuple(spec['gap']) if 'gap' in spec else label_gap(edges, (48, 40), z=False)   # an explicit gap wins
    width, height = grid_place(nodes, 'LR', gap, margin=label_w + 24, top=32)
    svg = Svg()
    route_all(nodes, edges, 'LR')
    rows = sorted({n.row for n in nodes.values()} | set(range(len(lanes))))
    row_h = {r: max([n.h for n in nodes.values() if n.row == r] or [44]) for r in rows}
    right = max(n.x + n.w for n in nodes.values()) + 40
    y = 12
    for i, l in enumerate(lanes):
        ns = [n for n in nodes.values() if n.row == i]
        top = min([n.y for n in ns] or [y]) - 20
        bot = max([n.y + n.h for n in ns] or [y + 44]) + 20
        if i % 2 == 0:
            svg.el('zones', 'rect', x=0, y=top, width=right, height=bot - top, fill=tint('ink', 0.02))
        svg.el('zones', 'line', x1=0, y1=bot, x2=right, y2=bot, stroke=RULE, stroke_width=1)
        if i == 0:
            svg.el('zones', 'line', x1=0, y1=top, x2=right, y2=top, stroke=RULE, stroke_width=1)
        svg.text('zones', 24, (top + bot) / 2 + 3, l.get('label', l['id']).upper(), size=8, mono=True, fill=MUTED, spacing='0.14em')
    draw_edges(svg, edges, nodes)
    for n in nodes.values():
        d = n.data
        node_box(svg, n.x, n.y, n.w, n.h, d.get('name', n.id), d.get('sub'), d.get('tag'), d.get('kind', 'default'))
    svg.legend = [(k, {'Component': 'Step'}.get(l, l)) for k, l in svg.legend]
    if any(nodes[e.a].row != nodes[e.b].row for e in edges):
        svg.legend.append((f'glyph:<rect x="{{x}}" y="{{y}}" width="20" height="12" fill="{tint("ink", 0.02)}" stroke="{RULE}" transform="translate(0,-6)"/>', 'Lane = owner'))
    svg.width = snap_up(right)
    return _finish(svg, nodes, right, height)


# ---------------------------------------------------------------- registry

_ARCH = {
    "type": "architecture", "slug": "auth-hop", "title": "Token check moves into the gateway",
    "desc": "Requests now pass the auth sidecar before reaching the orders API, which reads from Postgres and publishes to the event bus.",
    "direction": "LR",
    "nodes": [
        {"id": "web", "name": "Web app", "sub": "react", "tag": "UI", "kind": "input", "col": 0, "row": 0},
        {"id": "gw", "name": "API gateway", "sub": "envoy:443", "tag": "EDGE", "col": 1, "row": 0},
        {"id": "auth", "name": "Auth sidecar", "sub": "jwt verify", "tag": "NEW", "kind": "focal", "col": 1, "row": 1},
        {"id": "api", "name": "Orders API", "sub": "go:8080", "tag": "API", "col": 2, "row": 0},
        {"id": "db", "name": "Postgres", "sub": "orders", "tag": "DB", "kind": "store", "col": 3, "row": 0},
        {"id": "bus", "name": "Event bus", "sub": "kafka", "tag": "MQ", "kind": "external", "col": 3, "row": 1}
    ],
    "edges": [
        {"from": "web", "to": "gw", "label": "https"},
        {"from": "gw", "to": "auth", "label": "verify", "style": "accent"},
        {"from": "gw", "to": "api", "label": "grpc"},
        {"from": "api", "to": "db", "label": "sql"},
        {"from": "api", "to": "bus", "label": "publish", "style": "dashed"}
    ],
    "zones": [{"label": "Private network", "nodes": ["gw", "auth", "api", "db"]}]
}
_FLOW = {
    "type": "flowchart", "slug": "retry-policy", "title": "Retry policy after the change",
    "desc": "A failed call is retried with backoff only when the error is transient and the budget is not spent; otherwise it goes to the dead-letter queue.",
    "nodes": [
        {"id": "s", "name": "Call fails", "kind": "start", "col": 0, "row": 0},
        {"id": "t", "name": "Transient?", "kind": "decision", "col": 0, "row": 1},
        {"id": "b", "name": "Budget left?", "kind": "decision", "col": 0, "row": 2},
        {"id": "r", "name": "Retry with backoff", "sub": "2^n · jitter", "kind": "focal", "col": 0, "row": 3},
        {"id": "d", "name": "Dead-letter queue", "sub": "dlq.orders", "col": 1, "row": 2},
        {"id": "e", "name": "Done", "kind": "end", "col": 0, "row": 4}
    ],
    "edges": [
        {"from": "s", "to": "t"},
        {"from": "t", "to": "b", "label": "yes"},
        {"from": "t", "to": "d", "label": "no"},
        {"from": "b", "to": "r", "label": "yes", "style": "accent"},
        {"from": "b", "to": "d", "label": "no"},
        {"from": "r", "to": "e"}
    ]
}
_DEP = {
    "type": "dependency", "slug": "shared-core", "title": "Packages now converge on core",
    "desc": "Web, CLI and worker all depend on the extracted core package; core no longer imports web, which removes the old cycle.",
    "nodes": [
        {"id": "web", "name": "web", "sub": "app · internal", "rank": 0},
        {"id": "cli", "name": "cli", "sub": "bin · internal", "rank": 0},
        {"id": "worker", "name": "worker", "sub": "jobs · internal", "rank": 0},
        {"id": "core", "name": "core", "sub": "v2.0 · extracted", "kind": "focal", "rank": 1},
        {"id": "zod", "name": "zod", "sub": "v3.23 · npm", "kind": "external", "rank": 2},
        {"id": "pg", "name": "pg", "sub": "v8.11 · npm", "kind": "external", "rank": 2}
    ],
    "edges": [
        {"from": "web", "to": "core"}, {"from": "cli", "to": "core"}, {"from": "worker", "to": "core"},
        {"from": "core", "to": "zod"}, {"from": "core", "to": "pg"}, {"from": "worker", "to": "pg"}
    ]
}
_DEPLOY = {
    "type": "deployment", "slug": "read-replica", "title": "Orders DB gains a read replica",
    "desc": "Two API pods in the app subnet read from a new replica in the data subnet, which streams from the primary asynchronously.",
    "nodes": [
        {"id": "api", "name": "orders-api", "tag": "POD", "replicas": 2, "artifacts": [{"name": "orders-api", "version": "v1.9.0"}], "col": 0, "row": 0},
        {"id": "primary", "name": "orders-db", "tag": "MANAGED", "artifacts": [{"name": "postgres", "version": "16.2"}], "col": 1, "row": 0},
        {"id": "replica", "name": "orders-db-ro", "tag": "MANAGED", "accent": True, "artifacts": [{"name": "postgres", "version": "16.2"}], "col": 1, "row": 1}
    ],
    "paths": [
        {"from": "api", "to": "primary", "label": "tcp:5432"},
        {"from": "api", "to": "replica", "label": "tcp:5432 ro", "accent": True},
        {"from": "primary", "to": "replica", "label": "wal stream", "async": True}
    ],
    "zones": [{"label": "app subnet", "nodes": ["api"]}, {"label": "data subnet", "nodes": ["primary", "replica"]}]
}
_TREE = {
    "type": "tree", "slug": "billing-modules", "title": "billing/ after the split",
    "desc": "The billing package now splits into invoices, payments and a shared ledger module; payments holds the new refunds module.",
    "nodes": [
        {"id": "root", "name": "billing/", "sub": "package"},
        {"id": "inv", "name": "invoices/", "sub": "3 files", "parent": "root"},
        {"id": "pay", "name": "payments/", "sub": "5 files", "parent": "root"},
        {"id": "led", "name": "ledger/", "sub": "shared", "parent": "root"},
        {"id": "ref", "name": "refunds.ts", "sub": "new", "kind": "focal", "parent": "pay"},
        {"id": "cap", "name": "capture.ts", "parent": "pay"}
    ]
}
_ORG = {
    "type": "org-chart", "slug": "alert-routing", "title": "Who gets paged now",
    "desc": "Alerts enter through the on-call bot, which routes payments issues to the payments team and database issues to the platform team, with DBA approval for failover.",
    "nodes": [
        {"id": "bot", "name": "On-call bot", "invoke": "#alerts", "scope": "triage + route", "treatment": "front-door"},
        {"id": "pay", "name": "Payments team", "invoke": "@payments-oncall", "scope": "checkout, refunds", "parent": "bot"},
        {"id": "plat", "name": "Platform team", "invoke": "@platform-oncall", "scope": "db, queues", "parent": "bot"},
        {"id": "dba", "name": "DBA approval", "invoke": "@dba", "scope": "failover only", "treatment": "approval", "parent": "plat"},
        {"id": "gap", "name": "Search", "invoke": "unowned", "scope": "needs an owner", "treatment": "gap", "parent": "bot"}
    ]
}
_STATE = {
    "type": "state", "slug": "payment-states", "title": "Payment lifecycle with the new refund state",
    "desc": "A payment moves from pending to authorized to captured; captured payments can now be refunded, and failures end in failed.",
    "initial": "pending", "final": ["failed", "refunded"],
    "states": [
        {"id": "pending", "name": "Pending", "col": 1, "row": 0},
        {"id": "authorized", "name": "Authorized", "col": 2, "row": 0},
        {"id": "captured", "name": "Captured", "col": 3, "row": 0},
        {"id": "refunded", "name": "Refunded", "sub": "new", "focal": True, "col": 4, "row": 0},
        {"id": "failed", "name": "Failed", "col": 2, "row": 1}
    ],
    "transitions": [
        {"from": "pending", "to": "authorized", "event": "authorize", "guard": "3ds ok"},
        {"from": "authorized", "to": "captured", "event": "capture"},
        {"from": "captured", "to": "refunded", "event": "refund", "action": "notify", "accent": True},
        {"from": "pending", "to": "failed", "event": "decline"},
        {"from": "authorized", "to": "failed", "event": "timeout"}
    ]
}
_ER = {
    "type": "er", "slug": "shipments-model", "title": "Orders now have shipments",
    "desc": "An order has many shipments and each shipment has many tracking events; customers still own orders.",
    "entities": [
        {"name": "Customer", "fields": [{"name": "id", "pk": True}, {"name": "email"}], "col": 0, "row": 0},
        {"name": "Order", "fields": [{"name": "id", "pk": True}, {"name": "customer_id", "fk": True}, {"name": "total"}], "focal": True, "col": 1, "row": 0},
        {"name": "Shipment", "fields": [{"name": "id", "pk": True}, {"name": "order_id", "fk": True}, {"name": "carrier"}], "col": 2, "row": 0},
        {"name": "TrackingEvent", "fields": [{"name": "id", "pk": True}, {"name": "shipment_id", "fk": True}, {"name": "status"}], "col": 2, "row": 1}
    ],
    "relationships": [
        {"from": "Customer", "to": "Order", "card_from": "1", "card_to": "N", "label": "places"},
        {"from": "Order", "to": "Shipment", "card_from": "1", "card_to": "N"},
        {"from": "Shipment", "to": "TrackingEvent", "card_from": "1", "card_to": "N"}
    ]
}
_DB = {
    "type": "db-schema", "slug": "refunds-table", "title": "Migration 0042 adds refunds",
    "desc": "The new refunds table references payments with ON DELETE CASCADE, so deleting a payment deletes its refunds; orders stays RESTRICT.",
    "tables": [
        {"name": "orders", "columns": [{"name": "id", "type": "bigint", "chips": ["PK"]}, {"name": "status", "type": "text", "chips": ["NN"]}], "hidden": 6, "col": 0, "row": 0},
        {"name": "payments", "columns": [{"name": "id", "type": "bigint", "chips": ["PK"]}, {"name": "order_id", "type": "bigint", "chips": ["FK", "NN"]}, {"name": "amount", "type": "numeric(12,2)"}], "col": 1, "row": 0},
        {"name": "refunds", "columns": [{"name": "id", "type": "bigint", "chips": ["PK"]}, {"name": "payment_id", "type": "bigint", "chips": ["FK", "NN"]}, {"name": "reason", "type": "text"}, {"name": "created_at", "type": "timestamptz", "chips": ["NN"]}], "indexes": ["refunds_payment_id_idx"], "col": 2, "row": 0}
    ],
    "fks": [
        {"from": "payments.order_id", "to": "orders.id", "on_delete": "restrict"},
        {"from": "refunds.payment_id", "to": "payments.id", "on_delete": "cascade"}
    ]
}
_UML = {
    "type": "uml-class", "slug": "notifier-strategy", "title": "Notifier becomes an interface",
    "desc": "Email and Slack notifiers implement the new Notifier interface; the dispatcher owns a list of notifiers instead of calling email directly.",
    "direction": "TB",
    "classes": [
        {"name": "Dispatcher", "attrs": ["- notifiers: Notifier[]"], "ops": ["+ send(event): void"], "col": 0, "row": 0},
        {"name": "Notifier", "kind": "interface", "ops": ["+ notify(msg): Promise"], "focal": True, "col": 1, "row": 0},
        {"name": "EmailNotifier", "attrs": ["- smtp: Client"], "ops": ["+ notify(msg): Promise"], "col": 0, "row": 1},
        {"name": "SlackNotifier", "attrs": ["- webhook: URL"], "ops": ["+ notify(msg): Promise"], "col": 2, "row": 1}
    ],
    "rels": [
        {"from": "Notifier", "to": "Dispatcher", "kind": "aggregation", "mult_from": "0..*"},
        {"from": "EmailNotifier", "to": "Notifier", "kind": "implements"},
        {"from": "SlackNotifier", "to": "Notifier", "kind": "implements"}
    ]
}

_SWIM = {
    "type": "swimlane", "slug": "schema-migration-runbook", "title": "Who does what in a schema migration",
    "desc": "The developer opens the migration, CI runs it against a snapshot, the DBA approves, and SRE applies it during the window; the DBA approval is the new handoff.",
    "lanes": [{"id": "dev", "label": "Developer"}, {"id": "ci", "label": "CI"}, {"id": "dba", "label": "DBA"}, {"id": "sre", "label": "SRE"}],
    "steps": [
        {"id": "pr", "lane": "dev", "name": "Open migration PR", "sub": "0042_refunds.sql", "order": 0},
        {"id": "dry", "lane": "ci", "name": "Dry-run on snapshot", "sub": "pg 16 · 40 GB", "order": 1},
        {"id": "ok", "lane": "dba", "name": "Approve lock plan", "sub": "new gate", "kind": "focal", "order": 2},
        {"id": "apply", "lane": "sre", "name": "Apply in window", "sub": "02:00 UTC", "order": 3},
        {"id": "verify", "lane": "dev", "name": "Verify + close", "order": 4}
    ],
    "edges": [
        {"from": "pr", "to": "dry"},
        {"from": "dry", "to": "ok", "label": "plan", "style": "accent"},
        {"from": "ok", "to": "apply"},
        {"from": "apply", "to": "verify", "label": "done"}
    ]
}

TYPES = {
    'architecture': (render_architecture, _ARCH, 'components + connections; where a new piece sits, trust boundaries'),
    'flowchart': (render_flowchart, _FLOW, 'decision logic: validation, retry/fallback, routing branches'),
    'dependency': (render_dependency, _DEP, 'package/module deps with fan-in or a cycle introduced/broken'),
    'deployment': (render_deployment, _DEPLOY, 'where it runs: zones, pods, replicas, versions, ports'),
    'tree': (render_tree, _TREE, 'hierarchy: module/package restructure, decomposition'),
    'org-chart': (render_org_chart, _ORG, 'ownership/routing: CODEOWNERS, on-call, escalation'),
    'state': (render_state, _STATE, 'lifecycle of one entity: statuses, transitions, guards'),
    'er': (render_er, _ER, 'domain model: entities + cardinality (conceptual)'),
    'db-schema': (render_db_schema, _DB, 'physical schema: migration adds tables/columns/FKs/indexes'),
    'swimlane': (render_swimlane, _SWIM, 'who owns each step: cross-team process, handoffs, runbooks'),
    'uml-class': (render_uml_class, _UML, 'object model: interface extraction, inheritance vs composition'),
}
