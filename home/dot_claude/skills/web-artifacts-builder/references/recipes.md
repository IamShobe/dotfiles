# Recipes — copy-paste code

Read this only when building the specific feature. SKILL.md has the rules; this has the code.

## Mermaid component

The host only scans the initial static HTML for `<pre className="mermaid">`; React-injected nodes are never processed, so that path no-ops in a bundled app. Render it yourself. Use `theme: 'base'` so your `classDef` colors aren't overridden.

```tsx
import mermaid from 'mermaid'
let ready = false
function Mermaid({ chart, id }: { chart: string; id: string }) {
  const [svg, setSvg] = useState(''); const [err, setErr] = useState('')
  useEffect(() => {
    let alive = true
    if (!ready) { mermaid.initialize({ startOnLoad: false, theme: 'base', securityLevel: 'loose' }); ready = true }
    mermaid.parse(chart)                       // syntax-check first
      .then(() => mermaid.render(`m-${id}`, chart))
      .then(r => alive && setSvg(r.svg))
      .catch(e => alive && setErr(String(e?.message ?? e)))
    return () => { alive = false }
  }, [chart, id])
  if (err) return <pre className="text-xs text-red-600">mermaid: {err}</pre>
  return <div className="overflow-x-auto [&_svg]:mx-auto [&_svg]:max-w-full" dangerouslySetInnerHTML={{ __html: svg }} />
}
```

**Authoring a clear, color-coded chart** (shapes, `classDef` color-coding, theme palette, syntax, clarity rules) → **`mermaid.md`**. Non-negotiables: 4–7 nodes, color-code by role (not decoration), quote labels with spaces/punctuation, unique `id`, `securityLevel: 'loose'` for `<br/>`. The `.catch` surfaces errors instead of a blank box.

## Scroll container + TOC scaffold

**If this page also uses `RoughNotation`** (see `libraries.md`), it will visually detach from its text on scroll inside this `overflow-y-auto` div — RoughNotation has no listener on a non-window scroll ancestor. Use a plain CSS highlight `<span>` instead of `RoughNotation` anywhere inside this scroll container.

```tsx
const scrollRef = useRef<HTMLDivElement>(null)
<div ref={scrollRef} className="h-screen overflow-y-auto">
  <Scrollspy targetRef={scrollRef} offset={96} history={false} className="contents">
    <nav className="rail fixed left-5 top-1/2 -translate-y-1/2 hidden xl:flex flex-col gap-1.5">
      {SECTIONS.map(s => (
        <a key={s.id} href={`#${s.id}`} data-scrollspy-anchor={s.id}><span>{s.label}</span></a>
      ))}
    </nav>
  </Scrollspy>
  {/* pl-* reserves the rail's gutter; do NOT also add mx-auto — centering the
      max-w box in the full-width flex parent re-introduces the rail's offset
      as dead space and can push content under/behind the fixed rail. */}
  <main className="max-w-3xl pl-56 px-6 py-14">… <section id="core-shift">…</section> …</main>
</div>
```

Jitter-free active styling (never change `font-weight` on active — it reflows the rail):
```css
.rail a{display:flex;align-items:center;color:var(--muted);text-decoration:none;transition:color .18s}
.rail a > span{font-weight:600}                 /* reserve bold metrics for every item */
.rail a:not([data-active]) > span{font-weight:400}
.rail a::before{content:"";flex:0 0 auto;width:.9em;height:.9em;margin-right:.4rem;border-radius:99px;
  background:var(--border);transform:scale(.4);transition:background .18s,transform .18s}
.rail a[data-active]{color:var(--brand)}
.rail a[data-active]::before{background:var(--brand);transform:scale(1)}
```

## Pinned / scrollytelling visual

`position: fixed` (not `sticky`), `hidden xl:flex` with an inline fallback on narrow screens. Drive step changes with an `IntersectionObserver` over the section elements — a `scroll` listener won't fire in the iframe.

## Add a shadcn/ReUI component to the template

No network at build time — vendor once:
```bash
curl -sL https://reui.io/r/<name>.json | node -e 'JSON.parse(require("fs").readFileSync(0)).files.forEach(f=>require("fs").writeFileSync("template/src/components/ui/"+f.path.split("/").pop(),f.content))'
# or shadcn registry: https://ui.shadcn.com/r/<name>.json
```
Then `rm -rf <clone>` before rebuilding (stale-clone gotcha).
