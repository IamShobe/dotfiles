#!/usr/bin/env python3
"""Render explainer diagrams from JSON specs, then (optionally) convert them.

  render.py specs.json [--out DIR] [--artifact NAME]   # one spec object or an array
  render.py --list                                     # rendered types + one-line use
  render.py --example <type>                           # a valid spec to copy and edit

Each spec: {"type", "slug", "title", "desc", ...type fields}. Writes <DIR>/<slug>.html
(a bare accessible <svg>). With --artifact, runs diagram-to-jsx.sh on the results so
<NAME>/src/diagrams/<slug>.tsx exists and the import lines print. Exit 1 if any spec
failed; the message says what to change.
"""
from __future__ import annotations

import importlib
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True   # no __pycache__ inside installed skills

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from diagrams.core import SpecError, document  # noqa: E402

# Engine modules. Each defines TYPES = {type: (render_fn, example_spec, one_line_use)};
# render_fn(spec) -> (Svg, legend_y | None).
PAGE_W = 990   # usable figure width on a desktop explainer page
ENGINE_MODULES = ('graph', 'sequence', 'timeline', 'stack', 'charts', 'matrix')


def registry() -> dict:
    reg = {}
    for m in ENGINE_MODULES:
        try:
            mod = importlib.import_module(f'diagrams.{m}')
        except ModuleNotFoundError as e:
            if e.name == f'diagrams.{m}':
                continue
            raise
        reg.update(mod.TYPES)
    return reg


def render_one(spec: dict, reg: dict) -> str:
    t = spec.get('type')
    if t not in reg:
        raise SpecError(f"type '{t}' isn't rendered from a spec — draw it by hand from "
                        f"$DIAGRAM_DESIGN/references/type-{t}.md, or use one of: {', '.join(sorted(reg))}")
    slug = spec.get('slug', '')
    if not re.fullmatch(r'[a-z][a-z0-9-]*', slug):
        raise SpecError(f"slug '{slug}' must be kebab-case (it becomes the file and component name)")
    fn = reg[t][0]
    svg, legend_y = fn(spec)
    return document(svg, slug, spec.get('title', ''), spec.get('desc', ''), legend_y)


def main(argv: list[str]) -> int:
    reg = registry()
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    if argv[0] == '--list':
        for t in sorted(reg):
            print(f'{t:16} {reg[t][2]}')
        return 0
    if argv[0] == '--example':
        t = argv[1] if len(argv) > 1 else ''
        if t not in reg:
            print(f"no example for '{t}'. Rendered types: {', '.join(sorted(reg))}", file=sys.stderr)
            return 1
        print(json.dumps(reg[t][1], indent=2))
        return 0

    out_dir, artifact, files = '.', None, []
    it = iter(argv)
    for a in it:
        if a == '--out':
            out_dir = next(it)
        elif a == '--artifact':
            artifact = next(it)
        else:
            files.append(a)
    os.makedirs(out_dir, exist_ok=True)

    specs = []
    for f in files:
        data = json.load(open(f, encoding='utf-8'))
        specs.extend(data if isinstance(data, list) else [data])

    written, failed = [], 0
    for spec in specs:
        name = spec.get('slug') or spec.get('type') or '?'
        try:
            svg = render_one(spec, reg)
        except SpecError as e:
            print(f'✗ {name}: {e}', file=sys.stderr)
            failed += 1
            continue
        path = os.path.join(out_dir, f"{spec['slug']}.html")
        open(path, 'w', encoding='utf-8').write(svg)
        m = re.search(r'viewBox="0 0 ([\d.]+)', svg)
        vbw = float(m.group(1)) if m else 0
        if vbw > PAGE_W / 0.8:          # content column beside the TOC rail is ~PAGE_W px
            k = PAGE_W / vbw
            print(f"⚠ {name}: {int(vbw)}px wide, so on the page it shrinks to {k:.0%} and 12px names render at "
                  f"{12 * k:.0f}px. Cut steps, lower 'gap', or split it into two diagrams.", file=sys.stderr)
        written.append(path)
        if not artifact:
            print(f'✓ {path}')

    if artifact and written:
        r = subprocess.run(['bash', os.path.join(os.path.dirname(HERE), 'diagram-to-jsx.sh'), artifact, *written])
        failed += r.returncode != 0
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
