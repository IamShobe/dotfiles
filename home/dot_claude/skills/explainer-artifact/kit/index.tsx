// Explainer kit: page shell + building blocks. build.sh copies this file to
// src/explainer/index.tsx, so App.tsx imports everything from '@/explainer'.
//
// Every component is theme-driven (var(--…) only), reflows below md, and keeps
// wide content in its own overflow-x box, so App.tsx stays content-only.
import { Children, createContext, isValidElement, useContext, useRef } from 'react'
import type { ReactElement, ReactNode } from 'react'
import { Highlight, themes } from 'prism-react-renderer'
import { ArrowRight } from 'lucide-react'
import { Scrollspy } from '@/components/ui/scrollspy'
import { Theme } from '@/theme'

// ---------- source links ----------

export type Meta = { repo?: string; sha?: string; host?: string }
const MetaCtx = createContext<Meta>({})

/** Permalink for a repo path, or undefined when there is no remote to link to. */
export function sourceUrl(meta: Meta, path: string, lines?: string) {
  if (!meta.repo || !meta.sha) return undefined
  const host = meta.host ?? 'github.com'
  const blob = host.includes('gitlab') ? '-/blob' : host.includes('bitbucket') ? 'src' : 'blob'
  return `https://${host}/${meta.repo}/${blob}/${meta.sha}/${path}${lines ? `#L${lines.replace('-', host.includes('github') ? '-L' : '-')}` : ''}`
}

/** Inline source link: <Src path="src/a.ts" lines="12-24" />. Inline, never flex, so it flows in prose. */
export function Src({ path, lines, children }: { path: string; lines?: string; children?: ReactNode }) {
  const href = sourceUrl(useContext(MetaCtx), path, lines)
  const label = children ?? `${path.split('/').pop()}${lines ? `:${lines.split('-')[0]}` : ''}`
  const style = { color: 'var(--brand-ink)', fontSize: 'max(12px, 0.9em)' }
  return href
    ? <a className="mono underline decoration-dotted underline-offset-2" style={style} href={href} target="_blank" rel="noreferrer">{label}</a>
    : <code className="mono" style={style}>{label}</code>
}

// ---------- page shell ----------

type SectionProps = { id: string; title: string; takeaway?: ReactNode; children?: ReactNode }

const RAIL_CSS = `
.xk-rail a{display:flex;align-items:center;color:var(--ink-3);text-decoration:none;transition:color .18s;font-size:13px;line-height:1.35}
.xk-rail a>span{font-weight:600}.xk-rail a:not([data-active])>span{font-weight:400}
.xk-rail a::before{content:"";flex:0 0 auto;width:.9em;height:.9em;margin-right:.45rem;border-radius:99px;background:var(--border-hi);transform:scale(.4);transition:background .18s,transform .18s}
.xk-rail a[data-active]{color:var(--brand)}.xk-rail a[data-active]::before{background:var(--brand);transform:scale(1)}
.xk-prose{max-width:88ch}`

/**
 * The whole page: theme, fonts, own scroll container, hero, side-rail TOC.
 * Put <Section>s as DIRECT children: the TOC is built from them (3+ → rail at lg).
 */
export function Page({ meta = {}, eyebrow, title, thesis, pills = [], children }: {
  meta?: Meta; eyebrow?: ReactNode; title: ReactNode; thesis: ReactNode; pills?: ReactNode[]; children?: ReactNode
}) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const sections = Children.toArray(children)
    .filter((c): c is ReactElement<SectionProps> => isValidElement(c) && c.type === Section)
    .map(c => ({ id: c.props.id, title: c.props.title }))
  const rail = sections.length >= 3
  return (
    <MetaCtx.Provider value={meta}>
      <Theme />
      <link rel="stylesheet" precedence="default" href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&display=swap" />
      <style>{RAIL_CSS}</style>
      <div ref={scrollRef} className="h-screen overflow-y-auto" style={{ background: 'var(--bg)', color: 'var(--ink)', fontFamily: 'Geist, ui-sans-serif, system-ui, sans-serif' }}>
        {rail && (
          <Scrollspy targetRef={scrollRef} offset={96} history={false} className="contents">
            <nav className="xk-rail fixed left-5 top-1/2 -translate-y-1/2 hidden lg:flex flex-col gap-2 w-44" aria-label="Contents">
              {sections.map(s => <a key={s.id} href={`#${s.id}`} data-scrollspy-anchor={s.id}><span>{s.title}</span></a>)}
            </nav>
          </Scrollspy>
        )}
        <main className={`w-full max-w-[1280px] 2xl:max-w-[1480px] px-4 md:px-8 pb-24 ${rail ? 'lg:pl-56' : 'mx-auto'}`}>
          <header className="pt-10 md:pt-16 pb-8 md:pb-12">
            {eyebrow && <p className="mono text-xs uppercase tracking-[0.16em] mb-3" style={{ color: 'var(--brand)' }}>{eyebrow}</p>}
            <h1 className="text-3xl md:text-5xl font-semibold tracking-tight leading-tight" style={{ color: 'var(--ink)' }}>{title}</h1>
            <p data-thesis className="xk-prose text-lg md:text-xl mt-4 leading-relaxed" style={{ color: 'var(--ink-2)' }}>{thesis}</p>
            {pills.length > 0 && <div className="flex flex-wrap gap-2 mt-5">{pills.map((p, i) => <Chip key={i}>{p}</Chip>)}</div>}
          </header>
          {children}
        </main>
      </div>
    </MetaCtx.Provider>
  )
}

/** A top-level section. `takeaway` is the one line a skimmer must get. */
export function Section({ id, title, takeaway, children }: SectionProps) {
  return (
    <section id={id} className="py-10 md:py-14" style={{ borderTop: '1px solid var(--border)' }}>
      <h2 className="text-2xl md:text-3xl font-semibold tracking-tight" style={{ color: 'var(--ink)' }}>{title}</h2>
      {takeaway && <p data-takeaway className="xk-prose text-base md:text-lg mt-2 font-medium" style={{ color: 'var(--ink)' }}>{takeaway}</p>}
      <div className="mt-6 grid gap-6 min-w-0">{children}</div>
    </section>
  )
}

// ---------- text ----------

/** Body paragraph, capped at a readable measure. Keep it ≤ 3 lines. */
export function P({ children }: { children: ReactNode }) {
  return <p className="xk-prose leading-relaxed" style={{ color: 'var(--ink-2)' }}>{children}</p>
}

/** Highlight a word or phrase in prose (use instead of RoughNotation). */
export function Mark({ children }: { children: ReactNode }) {
  return <mark style={{ background: 'color-mix(in srgb, var(--signal) 35%, transparent)', color: 'inherit', padding: '0 .15em', borderRadius: 3 }}>{children}</mark>
}

/**
 * First use of a new word: <Term def="a rule set scoped to one account">perimeter</Term>.
 * Renders the word in bold with its plain-words definition inline, once. After that, use the bare word.
 */
export function Term({ def, children }: { def: ReactNode; children: ReactNode }) {
  return <><strong data-term style={{ color: 'var(--ink)' }}>{children}</strong> <span data-noprose style={{ color: 'var(--ink-3)' }}>({def})</span></>
}

/** Inline identifier: <Id>fetchUser()</Id>. */
export function Id({ children }: { children: ReactNode }) {
  return <code className="mono px-1 py-px rounded" style={{ fontSize: 'max(12px, 0.9em)', background: 'var(--brand-soft)', color: 'var(--brand-ink)' }}>{children}</code>
}

type Kind = 'add' | 'rm' | 'change' | 'keep' | 'neutral'
const KIND: Record<Kind, { fg: string; bg: string; sign: string }> = {
  add: { fg: 'var(--add)', bg: 'var(--add-soft)', sign: '+ ' },
  rm: { fg: 'var(--rm)', bg: 'var(--rm-soft)', sign: '− ' },
  change: { fg: 'var(--brand-ink)', bg: 'var(--brand-soft)', sign: '~ ' },
  keep: { fg: 'var(--ink-2)', bg: 'color-mix(in srgb, var(--signal) 22%, transparent)', sign: '' },
  neutral: { fg: 'var(--ink-2)', bg: 'color-mix(in srgb, var(--ink) 7%, transparent)', sign: '' },
}

/** Diff chip / pill. kind: add | rm | change | keep | neutral. Inline-block, safe in prose. */
export function Chip({ kind = 'neutral', children }: { kind?: Kind; children: ReactNode }) {
  const k = KIND[kind]
  return <span data-noprose className="mono inline-block text-xs px-2 py-0.5 rounded-full whitespace-nowrap align-middle" style={{ color: k.fg, background: k.bg }}>{k.sign}{children}</span>
}

// ---------- blocks ----------

/** Surface card. `label` is the small caps line on top. */
export function Card({ label, title, children, accent }: { label?: ReactNode; title?: ReactNode; children?: ReactNode; accent?: boolean }) {
  return (
    <div className="min-w-0 rounded-xl p-4 md:p-6" style={{ background: 'var(--surface)', border: `1px solid ${accent ? 'var(--brand)' : 'var(--border)'}` }}>
      {label && <p className="mono text-xs uppercase tracking-[0.14em] mb-2" style={{ color: accent ? 'var(--brand)' : 'var(--ink-3)' }}>{label}</p>}
      {title && <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--ink)' }}>{title}</h3>}
      <div className="grid gap-3 min-w-0" style={{ color: 'var(--ink-2)' }}>{children}</div>
    </div>
  )
}

/** Responsive grid of cards: 1 column, then `cols` from md. */
export function Grid({ cols = 2, children }: { cols?: 2 | 3 | 4; children: ReactNode }) {
  const c = { 2: 'md:grid-cols-2', 3: 'md:grid-cols-2 lg:grid-cols-3', 4: 'md:grid-cols-2 lg:grid-cols-4' }[cols]
  return <div className={`grid grid-cols-1 ${c} gap-4 min-w-0`}>{children}</div>
}

/** The core shift: old → new, stacked below md. */
export function BeforeAfter({ before, after, beforeLabel = 'Before', afterLabel = 'After' }: {
  before: ReactNode; after: ReactNode; beforeLabel?: ReactNode; afterLabel?: ReactNode
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-4 items-stretch min-w-0">
      <Card label={beforeLabel}>{before}</Card>
      <div className="hidden md:flex items-center" style={{ color: 'var(--ink-3)' }}><ArrowRight size={20} /></div>
      <Card label={afterLabel} accent>{after}</Card>
    </div>
  )
}

/** One-per-section "why this matters". */
export function Callout({ title, children }: { title?: ReactNode; children: ReactNode }) {
  return (
    <div className="rounded-lg p-4 md:p-5" style={{ background: 'var(--brand-soft)', borderLeft: '3px solid var(--brand)' }}>
      {title && <p className="font-semibold mb-1" style={{ color: 'var(--ink)' }}>{title}</p>}
      <div className="xk-prose" style={{ color: 'var(--ink-2)' }}>{children}</div>
    </div>
  )
}

/** Code block. `mark` = 1-based line numbers to call out. */
export function Code({ code, lang = 'tsx', title, mark = [] }: { code: string; lang?: string; title?: ReactNode; mark?: number[] }) {
  return (
    <figure className="min-w-0 rounded-lg overflow-hidden" style={{ background: 'var(--code-bg)', border: '1px solid var(--border)' }}>
      {title && <figcaption className="mono text-xs px-4 py-2" style={{ color: 'var(--code-ink)', opacity: 0.7, borderBottom: '1px solid color-mix(in srgb, var(--code-ink) 15%, transparent)' }}>{title}</figcaption>}
      <Highlight theme={themes.vsDark} code={code.replace(/^\n+|\s+$/g, '')} language={lang}>
        {({ tokens, getLineProps, getTokenProps }) => (
          <pre className="mono text-[13px] leading-6 p-4 overflow-x-auto" style={{ color: 'var(--code-ink)', background: 'transparent' }}>
            {tokens.map((line, i) => {
              const lp = getLineProps({ line })
              const on = mark.includes(i + 1)
              return <div key={i} {...lp} style={{ ...lp.style, background: on ? 'color-mix(in srgb, var(--signal) 18%, transparent)' : undefined, margin: '0 -1rem', padding: '0 1rem' }}>
                {line.map((t, j) => <span key={j} {...getTokenProps({ token: t })} />)}
              </div>
            })}
          </pre>
        )}
      </Highlight>
    </figure>
  )
}

/** Generic table. `mono` = column indexes rendered as identifiers. Scrolls in its own box. */
export function Table({ columns, rows, mono = [0] }: { columns: ReactNode[]; rows: ReactNode[][]; mono?: number[] }) {
  return (
    <div className="w-full min-w-0 overflow-x-auto rounded-lg" style={{ border: '1px solid var(--border)', background: 'var(--surface)' }}>
      <table className="w-full min-w-[560px] text-sm tabular-nums">
        <thead><tr>{columns.map((c, i) => <th key={i} className="text-left font-medium px-4 py-2.5" style={{ color: 'var(--ink-3)', borderBottom: '1px solid var(--border)' }}>{c}</th>)}</tr></thead>
        <tbody>{rows.map((r, i) => (
          <tr key={i} style={{ borderTop: i ? '1px solid var(--border)' : undefined }}>
            {r.map((cell, j) => <td key={j} className={`px-4 py-2.5 align-top ${mono.includes(j) ? 'mono text-[13px]' : ''}`} style={{ color: j === 0 ? 'var(--ink)' : 'var(--ink-2)' }}>{cell}</td>)}
          </tr>
        ))}</tbody>
      </table>
    </div>
  )
}

/** Interface changes, old → new. A row with only `after` is added, only `before` is removed. */
export function Changes({ rows }: { rows: { name: ReactNode; before?: ReactNode; after?: ReactNode; note?: ReactNode }[] }) {
  return <Table columns={['', 'Before', 'After', '']} mono={[1, 2]} rows={rows.map(r => [
    <span className="font-medium">{r.name}</span>,
    r.before ? <span style={{ color: 'var(--rm)' }}>{r.before}</span> : <span style={{ color: 'var(--ink-3)' }}>—</span>,
    r.after ? <span style={{ color: 'var(--add)' }}>{r.after}</span> : <span style={{ color: 'var(--ink-3)' }}>—</span>,
    <span className="grid gap-1 justify-items-start"><Chip kind={!r.before ? 'add' : !r.after ? 'rm' : 'change'}>{!r.before ? 'added' : !r.after ? 'removed' : 'changed'}</Chip>{r.note}</span>,
  ])} />
}

/** Deprecations: gone for good vs kept as fallback (don't build on those). */
export function Deprecations({ removed = [], kept = [] }: { removed?: { what: ReactNode; why: ReactNode }[]; kept?: { what: ReactNode; why: ReactNode }[] }) {
  return (
    <div className="grid gap-4 min-w-0">
      {removed.length > 0 && <Table columns={['Removed', 'Why']} rows={removed.map(r => [r.what, r.why])} />}
      {kept.length > 0 && (
        <Card label="Kept as fallback · don't build on these">
          <ul className="grid gap-2">{kept.map((k, i) => <li key={i}><Chip kind="keep">{k.what}</Chip> <span className="ml-1">{k.why}</span></li>)}</ul>
        </Card>
      )}
    </div>
  )
}

/** Numbered how-to. Each step: title, optional body, optional code. */
export function Steps({ items }: { items: { title: ReactNode; body?: ReactNode; code?: string; lang?: string }[] }) {
  return (
    <ol className="grid gap-5 min-w-0">
      {items.map((s, i) => (
        <li key={i} className="grid grid-cols-[2rem_1fr] gap-3 min-w-0">
          <span className="mono text-sm w-7 h-7 rounded-full grid place-items-center" style={{ background: 'var(--brand-soft)', color: 'var(--brand-ink)' }}>{i + 1}</span>
          <div className="grid gap-2 min-w-0">
            <p className="font-medium" style={{ color: 'var(--ink)' }}>{s.title}</p>
            {s.body && <div className="xk-prose" style={{ color: 'var(--ink-2)' }}>{s.body}</div>}
            {s.code && <Code code={s.code} lang={s.lang} />}
          </div>
        </li>
      ))}
    </ol>
  )
}

/** Frame for a converted diagram (or screenshot) with an optional caption. */
export function Figure({ caption, children }: { caption?: ReactNode; children: ReactNode }) {
  return (
    <figure className="min-w-0 rounded-xl p-2 md:p-4" style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
      {children}
      {caption && <figcaption className="text-sm mt-2 px-2" style={{ color: 'var(--ink-3)' }}>{caption}</figcaption>}
    </figure>
  )
}
