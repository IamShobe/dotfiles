"""Sequence engine: actors with dashed lifelines, time-ordered messages, derived
activation bars, one combined fragment (alt / opt / loop), notes.

Grammar: diagram-design references/type-sequence.md; geometry from its
example-sequence*.html (56px actor heads, activation w=8, self-call 36x32 U loop,
fragment tab 40x16, guard under the tab, dashed alt divider).

Activations are derived, never authored: a call/http message opens a bar on the
receiver; the first later return/headline from that receiver back to the caller
closes it. Bars stack (+4px) when an active actor is called again. Anything left
open is closed after the actor's last message, and at the end of its fragment
region, so fragments always enclose exactly their steps.
"""
from __future__ import annotations

from .core import (ACCENT, EDGE_STYLES, LINK, MUTED, NODE_KINDS, PAPER, SANS, SOFT, SpecError, Svg, budget,
                   need, node_box, ortho_path, snap, snap_up, text_width, tint, _n)

# ---------- constants (4px grid) ----------

MARGIN = 32
ACTOR_Y = 32
ACTOR_H = 56
MIN_GAP = 160            # lifeline spacing floor
BAR_W = 8
STACK = 4                # x offset per nested activation level
BAR_REACH = 8            # worst-case bar protrusion right of a lifeline
LABEL_CLEAR = 12         # label mask to nearest bar edge / lifeline
SELF_W, SELF_H = 36, 32  # self-call loop
MAX_LABEL = 28

KINDS = ('call', 'http', 'return', 'async', 'headline')
STYLE = {'call': 'default', 'http': 'link', 'return': 'dashed', 'async': 'async', 'headline': 'accent'}
LEGEND = {'call': 'Call', 'http': 'HTTP / API call', 'return': 'Return', 'async': 'Async (fire-and-forget)',
          'headline': 'Headline response'}
LABEL_FILL = {'http': LINK, 'headline': ACCENT}
ACTOR_KINDS = ('default', 'focal', 'external', 'store', 'input', 'optional')

LIFELINE = tint('ink', 0.22)
FRAME_STROKE = tint('ink', 0.22)

# vertical gap from the previous element's bottom to the next element's top line
GAP = {
    'msg':  {'top': 48, 'msg': 40, 'self': 40, 'guard': 32, 'frame': 36, 'note': 36},
    'self': {'top': 40, 'msg': 32, 'self': 32, 'guard': 24, 'frame': 28, 'note': 28},
    'note': {'top': 24, 'msg': 16, 'self': 16, 'guard': 12, 'frame': 20, 'note': 16},
    'frag': {'top': 24, 'msg': 28, 'self': 28, 'guard': 16, 'frame': 24, 'note': 24},
}


def _label_w(s: str) -> int:
    """Mask width core.label() will draw, plus letter-spacing (0.06em) it doesn't count."""
    s = s.upper()
    return snap_up(text_width(s, 8, True) + 8 + 0.48 * len(s))


def _guard_w(g: str) -> int:
    """Mask width of a guard label (mono 8, 0.04em spacing, mixed case)."""
    return snap_up(text_width(g, 8, True) + 8 + 0.32 * len(g))


# ---------- spec → normalized steps ----------

class _Ctx:
    def __init__(self, ids):
        self.ids = ids
        self.msgs = 0
        self.frags = []          # (op, n_regions)
        self.headlines = 0


def _actor(ctx: _Ctx, a, where: str) -> int:
    if a not in ctx.ids:
        raise SpecError(f"{where}: actor '{a}' isn't declared — use one of: {', '.join(ctx.ids)}")
    return ctx.ids.index(a)


def _norm(steps, ctx: _Ctx, depth: int, where: str) -> list:
    if not isinstance(steps, list) or not steps:
        raise SpecError(f'{where or "sequence"}: "steps" must be a non-empty list of messages / fragments / notes')
    out = []
    for n, s in enumerate(steps, 1):
        w = f'{where} step {n}'.strip()
        if not isinstance(s, dict):
            raise SpecError(f'{w}: each step is an object — {{"from","to","label"}}, {{"fragment",...}} or {{"note",...}}')
        if 'fragment' in s:
            op = s['fragment']
            if op not in ('alt', 'opt', 'loop'):
                raise SpecError(f"{w}: fragment '{op}' isn't supported — use alt, opt or loop "
                                f"(par/critical/break/ref are out of scope; split the diagram)")
            if depth >= 2:
                raise SpecError(f'{w}: fragments nest at most 1 level deep — move this {op} out, or split into two diagrams')
            regions = s.get('regions')
            if not isinstance(regions, list) or not regions:
                raise SpecError(f'{w}: {op} needs "regions": [{{"guard": "[condition]", "steps": [...]}}]')
            if op == 'alt':
                if len(regions) == 1:
                    raise SpecError(f'{w}: an alt with one region is an opt — change "fragment" to "opt" or add an [else] region')
                budget(f'{w}: alt regions', len(regions), 2, 'split the extra branch into its own diagram')
            elif len(regions) != 1:
                raise SpecError(f'{w}: {op} takes exactly one region (got {len(regions)}) — use alt for branches')
            ctx.frags.append((op, len(regions)))
            regs = []
            for k, r in enumerate(regions):
                guard = str(r.get('guard') or ('[else]' if k else '')).strip()
                if not guard:
                    raise SpecError(f'{w}: region 1 needs a "guard", e.g. "[token expired]" or "[for each batch]"')
                if not guard.startswith('['):
                    guard = f'[{guard}]'
                h0 = ctx.headlines
                body = _norm(r.get('steps'), ctx, depth + 1, f'{w} region {k + 1}')
                regs.append({'guard': guard, 'steps': body, 'headline': ctx.headlines > h0})
            if op == 'alt' and all(r['headline'] for r in regs):
                raise SpecError(f'{w}: headline (accent) is on both alt branches — keep it on the happy path only, '
                                f'make the other a "return"')
            touched = set()
            for r in regs:
                touched |= _touched(r['steps'])
            over = s.get('over')
            if over:
                over_i = {_actor(ctx, a, f'{w} "over"') for a in over}
                missing = touched - over_i
                if missing:
                    raise SpecError(f'{w}: steps inside the {op} touch {", ".join(ctx.ids[i] for i in sorted(missing))} '
                                    f'— add them to "over" (or drop "over" to derive it)')
                touched = over_i
            out.append({'t': 'frag', 'op': op, 'lo': min(touched), 'hi': max(touched), 'regions': regs,
                        'touched': touched})
        elif 'note' in s:
            text = str(s['note']).strip()
            over = s.get('over')
            if not text or not over:
                raise SpecError(f'{w}: a note needs text and "over": [actorId, ...]')
            if len(text) > 48:
                raise SpecError(f'{w}: note is {len(text)} chars — keep it ≤48; put the rest in prose')
            idx = sorted({_actor(ctx, a, f'{w} note') for a in over})
            out.append({'t': 'note', 'text': text, 'lo': idx[0], 'hi': idx[-1]})
        else:
            for k in ('from', 'to', 'label'):
                if k not in s:
                    raise SpecError(f'{w}: a message needs "from", "to" and "label" (missing "{k}")')
            kind = s.get('kind', 'call')
            if kind not in KINDS:
                raise SpecError(f"{w}: kind '{kind}' unknown — use one of: {', '.join(KINDS)}")
            a, b = _actor(ctx, s['from'], w), _actor(ctx, s['to'], w)
            label = str(s['label']).strip()
            if not label:
                raise SpecError(f'{w}: empty label — say what is sent, e.g. "POST /token"')
            if len(label) > MAX_LABEL:
                raise SpecError(f'{w}: label "{label}" is {len(label)} chars — shorten to ≤{MAX_LABEL} '
                                f'(e.g. drop the payload detail; explain it in prose)')
            if a == b and kind in ('return', 'headline'):
                raise SpecError(f'{w}: a self-message can\'t be a {kind} — use kind "call" (or "async")')
            ctx.msgs += 1
            if kind == 'headline':
                ctx.headlines += 1
            out.append({'t': 'self' if a == b else 'msg', 'a': a, 'b': b, 'label': label, 'kind': kind})
    return out


def _touched(steps) -> set:
    t = set()
    for s in steps:
        if s['t'] in ('msg', 'self'):
            t |= {s['a'], s['b']}
        elif s['t'] == 'note':
            t |= set(range(s['lo'], s['hi'] + 1))
        else:
            t |= set(range(s['lo'], s['hi'] + 1))
    return t


def _walk(steps):
    for s in steps:
        yield s
        if s['t'] == 'frag':
            for r in s['regions']:
                yield from _walk(r['steps'])


# ---------- horizontal layout ----------

def _spacing(actors, widths, steps) -> list[int]:
    """Lifeline centres. Each gap is sized from the widest thing that must sit inside it."""
    n = len(actors)
    need_ = [max(MIN_GAP, widths[i] / 2 + widths[i + 1] / 2 + 24) for i in range(n - 1)]
    lab_need = lambda s: _label_w(s['label']) + 2 * (LABEL_CLEAR + BAR_REACH)
    spanning, wide_notes = [], []
    for s in _walk(steps):
        if s['t'] == 'self' and s['a'] < n - 1:
            need_[s['a']] = max(need_[s['a']], BAR_REACH + SELF_W + 8 + _label_w(s['label']) + 2 * LABEL_CLEAR + BAR_REACH)
        elif s['t'] == 'msg':
            lo, hi = sorted((s['a'], s['b']))
            if hi - lo == 1:
                need_[lo] = max(need_[lo], lab_need(s))
            else:
                spanning.append(s)
        elif s['t'] == 'frag' and s['lo'] > 0:
            # guards sit left of the first participating lifeline: the gap before it must hold one
            gw = max(_guard_w(r['guard']) for r in s['regions'])
            need_[s['lo'] - 1] = max(need_[s['lo'] - 1], gw + 20 + 16 + BAR_REACH + 16)
        elif s['t'] == 'note':
            nw = _note_w(s['text'])
            if s['lo'] == s['hi']:
                i = s['lo']
                if i > 0:
                    need_[i - 1] = max(need_[i - 1], nw / 2 + 24 + BAR_REACH)
                if i < n - 1:
                    need_[i] = max(need_[i], nw / 2 + 24 + BAR_REACH)
            else:
                wide_notes.append(s)
    # a label crossing several lifelines goes in the roomiest gap it spans (ties: next to the sender)
    for s in sorted(spanning, key=lab_need, reverse=True):
        lo, hi = sorted((s['a'], s['b']))
        home = lo if s['a'] < s['b'] else hi - 1
        g = max(range(lo, hi), key=lambda k: (need_[k], k == home))
        need_[g] = max(need_[g], lab_need(s))
        s['gap'] = g
    for s in wide_notes:
        short = _note_w(s['text']) - 48 - sum(need_[s['lo']:s['hi']])
        if short > 0:
            per = short / (s['hi'] - s['lo'])
            for k in range(s['lo'], s['hi']):
                need_[k] += per
    cx = [0]
    for g in need_:
        cx.append(cx[-1] + snap_up(g))
    return cx


def _note_w(text: str) -> int:
    return max(96, snap_up(text_width(text, 10) + 24, 8))


# ---------- vertical layout + drawing ----------

class _Act:
    __slots__ = ('actor', 'caller', 'top', 'bottom', 'level', 'last')

    def __init__(self, actor, caller, y, level):
        self.actor, self.caller, self.level = actor, caller, level
        self.top, self.bottom, self.last = y - 4, None, y

    def close(self, y):
        self.bottom = max(self.bottom or 0, y)

    def autoclose(self):
        self.close(snap_up(max(self.last + 8, self.top + 20)))


class _Layout:
    def __init__(self, svg: Svg, cx: list, widths: list):
        self.svg, self.cx, self.widths = svg, cx, widths
        self.stacks = [[] for _ in cx]
        self.acts: list[_Act] = []
        self.frames = []
        self.exts = [[10 ** 9, -10 ** 9]]
        self.used = set()
        self.y, self.prev = ACTOR_Y + ACTOR_H, 'top'

    # extents
    def ext(self, x0, x1):
        for e in self.exts:
            e[0], e[1] = min(e[0], x0), max(e[1], x1)

    # bar edge of actor i that faces x-direction `right`
    def edge(self, i, right: bool, act: _Act | None = None):
        act = act or (self.stacks[i][-1] if self.stacks[i] else None)
        if act is None:
            return self.cx[i]
        left = self.cx[i] - BAR_W / 2 + STACK * act.level
        return left + BAR_W if right else left

    def touch(self, i, y):
        if self.stacks[i]:
            self.stacks[i][-1].last = max(self.stacks[i][-1].last, y)

    def advance(self, what):
        self.y = snap(self.y + GAP[what][self.prev])
        return self.y

    def steps(self, steps, depth=0):
        for s in steps:
            getattr(self, 'do_' + s['t'])(s, depth)

    def do_msg(self, s, depth):
        y = self.advance('msg')
        a, b, kind = s['a'], s['b'], s['kind']
        rightward = b > a
        if kind in ('call', 'http'):
            x1 = self.edge(a, rightward)
            act = _Act(b, a, y, len(self.stacks[b]))
            self.stacks[b].append(act)
            self.acts.append(act)
            x2 = self.edge(b, not rightward)
        elif kind in ('return', 'headline'):
            st = self.stacks[a]
            hit = next((k for k in range(len(st) - 1, -1, -1) if st[k].caller == b), None)
            if hit is None:
                x1 = self.edge(a, rightward)
            else:
                x1 = self.edge(a, rightward, st[hit])
                for act in st[hit:]:
                    act.close(y + 4)
                del st[hit:]
            x2 = self.edge(b, not rightward)
        else:
            x1, x2 = self.edge(a, rightward), self.edge(b, not rightward)
        self.touch(a, y)
        self.touch(b, y)
        stroke, width, dash, mk = EDGE_STYLES[STYLE[kind]]
        self.svg.el('edges', 'line', x1=_n(x1), y1=y, x2=_n(x2), y2=y, stroke=stroke, stroke_width=width,
                    stroke_dasharray=dash, marker_end=self.svg.marker(mk))
        self.used.add(kind)
        lo, hi = sorted((x1, x2))
        g = s.get('gap', min(a, b))
        l, r = max(lo, self.cx[g]), min(hi, self.cx[g + 1])
        lx = snap((l + r) / 2)
        _, _, w, _ = self.svg.label(lx, y - 10, s['label'], fill=LABEL_FILL.get(kind, SOFT))
        self.ext(min(lo, lx - w / 2), max(hi, lx + w / 2))
        self.prev = 'msg'

    def do_self(self, s, depth):
        y = self.advance('self')
        a, kind = s['a'], s['kind']
        bx = self.edge(a, True)
        rx, y2 = bx + SELF_W, y + SELF_H
        stroke, width, dash, mk = EDGE_STYLES[STYLE[kind]]
        self.svg.el('edges', 'path', d=ortho_path([(bx, y), (rx, y), (rx, y2), (bx, y2)]), fill='none', stroke=stroke,
                    stroke_width=width, stroke_dasharray=dash, marker_end=self.svg.marker(mk))
        self.used.add(kind)
        lx = rx + 12
        _, _, w, _ = self.svg.label(lx, y + SELF_H / 2 + 3, s['label'], anchor='start', fill=LABEL_FILL.get(kind, SOFT))
        self.ext(bx, lx - 4 + w)
        self.touch(a, y2)
        self.y, self.prev = y2, 'self'

    def do_note(self, s, depth):
        y = self.advance('note')
        lo, hi = self.cx[s['lo']], self.cx[s['hi']]
        w = max(_note_w(s['text']), snap_up(hi - lo + 48, 8))
        x = snap((lo + hi) / 2 - w / 2)
        self.svg.el('nodes', 'rect', x=x, y=y, width=w, height=24, rx=4, fill=PAPER)
        self.svg.el('nodes', 'rect', x=x, y=y, width=w, height=24, rx=4, fill=tint('ink', 0.04),
                    stroke=tint('ink', 0.22), stroke_width=0.8)
        self.svg.text('nodes', x + w / 2, y + 16, s['text'], size=10, fill=MUTED, anchor='middle')
        self.ext(x, x + w)
        for i in range(s['lo'], s['hi'] + 1):
            self.touch(i, y + 24)
        self.y, self.prev = y + 24, 'note'

    def do_frag(self, s, depth):
        top = self.advance('frag')
        snapshot = [list(st) for st in self.stacks]
        ends, guards, dividers = [], [], []
        self.exts.append([10 ** 9, -10 ** 9])
        for k, r in enumerate(s['regions']):
            if k == 0:
                gy = top + 32
            else:
                dy = snap(self.y + 24)
                dividers.append(dy)
                gy = dy + 24
            guards.append((gy, r['guard']))
            self.y, self.prev = gy, 'guard'
            self.stacks = [list(st) for st in snapshot]
            self.steps(r['steps'], depth + 1)
            for i, st in enumerate(self.stacks):   # region-local bars close inside the frame
                for act in st:
                    if act not in snapshot[i]:
                        act.autoclose()
            ends.append([[a for a in st if a in snapshot[i]] for i, st in enumerate(self.stacks)])
        inner = self.exts.pop()
        self.stacks = [[a for a in snapshot[i] if any(a in e[i] for e in ends)] for i in range(len(self.cx))]
        bottom = snap_up(self.y + 24)
        inset = 12 if depth else 0
        gw = max(_guard_w(r['guard']) for r in s['regions'])
        x0 = min(self.cx[s['lo']] - self.widths[s['lo']] / 2 + inset, inner[0] - 12,
                 self.cx[s['lo']] - BAR_W / 2 - 8 - gw - 8)   # guard never crosses a lifeline / bar
        x1 = max(self.cx[s['hi']] + self.widths[s['hi']] / 2 - inset, inner[1] + 12)
        x0, x1 = snap(x0 - 2), snap_up(x1)
        self.frames.append((depth, x0, top, x1, bottom, s['op'], guards, dividers))
        self.ext(x0, x1)
        self.y, self.prev = bottom, 'frame'

    def draw_frames(self):
        svg = self.svg
        for depth, x0, y0, x1, y1, op, guards, dividers in sorted(self.frames, key=lambda f: f[0]):
            svg.el('zones', 'rect', x=_n(x0), y=y0, width=_n(x1 - x0), height=y1 - y0, rx=4, fill=tint('ink', 0.02),
                   stroke=FRAME_STROKE, stroke_width=1)
            tw = max(40, snap_up(text_width(op.upper(), 8, True) + 0.96 * len(op) + 16))
            svg.el('labels', 'rect', x=_n(x0), y=y0, width=tw, height=16, rx=2, fill=PAPER, stroke=FRAME_STROKE,
                   stroke_width=1)
            svg.text('labels', x0 + tw / 2, y0 + 12, op.upper(), size=8, mono=True, fill=MUTED, anchor='middle',
                     spacing='0.12em')
            for gy, g in guards:
                svg.label(x0 + 12, gy, g, anchor='start', fill=MUTED, upper=False, spacing='0.04em')
            for dy in dividers:
                svg.el('zones', 'line', x1=_n(x0 + 8), y1=dy, x2=_n(x1 - 8), y2=dy, stroke=tint('ink', 0.2),
                       stroke_width=1, stroke_dasharray='4,3')


def _draw(spec, actors, widths, steps, cx, shift) -> tuple[Svg, int, list]:
    svg = Svg()
    cx = [c + shift for c in cx]
    L = _Layout(svg, cx, widths)
    for i, a in enumerate(actors):
        L.ext(cx[i] - widths[i] / 2, cx[i] + widths[i] / 2)
    L.steps(steps)
    for st in L.stacks:
        for act in st:
            act.autoclose()
    bottom = snap_up(L.y + 32)
    L.draw_frames()
    # lifelines under everything, bars before messages so arrowheads land on their edges
    lines = [f'<line x1="{c}" y1="{ACTOR_Y + ACTOR_H}" x2="{c}" y2="{bottom}" stroke="{LIFELINE}" stroke-width="1" '
             f'stroke-dasharray="3,3"/>' for c in cx]
    bars = []
    for act in sorted(L.acts, key=lambda a: a.level):
        x = cx[act.actor] - BAR_W / 2 + STACK * act.level
        bars.append(f'<rect x="{_n(x)}" y="{act.top}" width="{BAR_W}" height="{act.bottom - act.top}" fill="{PAPER}"/>')
        bars.append(f'<rect x="{_n(x)}" y="{act.top}" width="{BAR_W}" height="{act.bottom - act.top}" '
                    f'fill="{tint("ink", 0.06)}" stroke="{MUTED}" stroke-width="0.8"/>')
    svg.layers['zones'][:0] = lines
    svg.layers['edges'][:0] = bars
    for i, a in enumerate(actors):
        node_box(svg, cx[i] - widths[i] / 2, ACTOR_Y, widths[i], ACTOR_H, a['name'], a.get('sub'), a.get('tag'),
                 kind=a['kind'], legend=False)
    # legend: actor treatments actually used, activation, fragment, message kinds actually used
    for kind in dict.fromkeys(a['kind'] for a in actors):
        if kind != 'default':
            svg.key(f'node:{kind}', NODE_KINDS[kind][3].replace('Focal / changed', 'Focal / changed actor'))
    if L.acts:
        svg.key(f'glyph:<g transform="translate({{x}} {{y}})"><rect x="8" y="-9" width="{BAR_W}" height="18" '
                f'fill="{tint("ink", 0.06)}" stroke="{MUTED}" stroke-width="0.8"/></g>', 'Activation')
    if L.frames:
        svg.key(f'glyph:<g transform="translate({{x}} {{y}})"><rect x="0" y="-7" width="22" height="14" rx="2" '
                f'fill="{tint("ink", 0.02)}" stroke="{FRAME_STROKE}" stroke-width="1"/><rect x="0" y="-7" width="10" '
                f'height="6" rx="1" fill="{PAPER}" stroke="{FRAME_STROKE}" stroke-width="1"/></g>', 'Fragment (alt / opt / loop)')
    for k in KINDS:
        if k in L.used:
            svg.key(f'line:{STYLE[k]}', LEGEND[k])
    return svg, bottom, L.exts[0]


def render(spec: dict):
    need(spec, 'actors', 'steps')
    actors = spec['actors']
    if not isinstance(actors, list) or len(actors) < 2:
        raise SpecError('sequence needs "actors": at least 2 of {"id","name","sub"?,"kind"?}')
    budget('sequence lifelines', len(actors), 5, 'merge actors that always act together, or split into overview + detail')
    ids = []
    for n, a in enumerate(actors, 1):
        if not isinstance(a, dict) or not a.get('id') or not a.get('name'):
            raise SpecError(f'actor {n}: needs "id" and "name" (plus optional "sub", "tag", "kind")')
        if a['id'] in ids:
            raise SpecError(f"actor id '{a['id']}' is used twice — ids must be unique")
        ids.append(a['id'])
        a.setdefault('kind', 'default')
        if a['kind'] not in ACTOR_KINDS:
            raise SpecError(f"actor '{a['id']}': kind '{a['kind']}' unknown — use one of: {', '.join(ACTOR_KINDS)}")
        if a.get('tag') and len(a['tag']) > 5:
            raise SpecError(f"actor '{a['id']}': tag '{a['tag']}' is too long — ≤5 chars, e.g. API, EXT, DB")
    ctx = _Ctx(ids)
    steps = _norm(spec['steps'], ctx, 0, '')
    budget('sequence messages', ctx.msgs, 12, 'split into overview (happy path) + detail (failure / refresh path)')
    ops = ctx.frags
    if len(ops) > 1 and not (len(ops) == 2 and all(op in ('opt', 'loop') for op, _ in ops)):
        raise SpecError(f'sequence fragments: {len(ops)} ({", ".join(o for o, _ in ops)}) — one fragment per diagram; '
                        f'two only if both are single-region opt/loop. Split the second branch into its own diagram')
    focal = sum(a['kind'] == 'focal' for a in actors)
    budget('headline messages', ctx.headlines, 2, 'keep accent on the one primary success response; make the rest "return"')
    budget('accent elements (focal actors + headline messages)', focal + ctx.headlines, 2,
           'drop "focal" from an actor or turn a headline into a plain "return"')

    widths = []
    for a in actors:
        w = max(text_width(a['name'], 12, weight=600), text_width(a.get('sub') or '', 9, True)) + 32
        if a.get('tag'):
            w = max(w, text_width(a['name'], 12, weight=600) + 2 * (snap_up(text_width(a['tag'].upper(), 7, True) + 10) + 16))
        widths.append(max(144, snap_up(w, 8)))
    cx = _spacing(actors, widths, steps)
    # dry run for the content extents, then draw for real shifted into the margin
    _, _, (xmin, _) = _draw(spec, actors, widths, steps, cx, 0)
    shift = snap_up(MARGIN - xmin)
    svg, bottom, (_, xmax) = _draw(spec, actors, widths, steps, cx, shift)
    svg.width = snap_up(xmax + MARGIN)
    legend_y = bottom + 24
    svg.height = legend_y
    return svg, legend_y


EXAMPLE = {
    'type': 'sequence',
    'slug': 'orders-token-refresh',
    'title': 'Orders API refreshes expired tokens server-side',
    'desc': 'The Orders API now loads the session from Redis and, when the access token has expired, refreshes it '
            'with the auth service before answering, instead of bouncing a 401 back to the web app.',
    'actors': [
        {'id': 'web', 'name': 'Web app', 'sub': 'React SPA', 'kind': 'input'},
        {'id': 'api', 'name': 'Orders API', 'sub': 'session middleware', 'tag': 'API', 'kind': 'focal'},
        {'id': 'redis', 'name': 'Session cache', 'sub': 'Redis', 'kind': 'store'},
        {'id': 'auth', 'name': 'Auth service', 'sub': 'OAuth · /token', 'kind': 'external'},
    ],
    'steps': [
        {'from': 'web', 'to': 'api', 'label': 'GET /orders + cookie', 'kind': 'http'},
        {'from': 'api', 'to': 'redis', 'label': 'load session'},
        {'from': 'redis', 'to': 'api', 'label': 'tokens + expiry', 'kind': 'return'},
        {'fragment': 'alt', 'regions': [
            {'guard': '[access token expired]', 'steps': [
                {'from': 'api', 'to': 'auth', 'label': 'POST /token · refresh', 'kind': 'http'},
                {'from': 'auth', 'to': 'api', 'label': 'new access + refresh', 'kind': 'return'},
                {'from': 'api', 'to': 'redis', 'label': 'save session', 'kind': 'async'},
            ]},
            {'guard': '[else]', 'steps': [
                {'from': 'api', 'to': 'api', 'label': 'verify JWT'},
            ]},
        ]},
        {'from': 'api', 'to': 'web', 'label': '200 · orders', 'kind': 'headline'},
    ],
}

TYPES = {'sequence': (render, EXAMPLE,
                      'time-ordered messages between ≤5 actors (API calls, auth/refresh paths, one alt/opt/loop branch)')}
