// Page kit: page shell + building blocks, shipped in the template at src/kit,
// so App.tsx imports everything from '@/kit'.
//
// Every component is theme-driven (var(--…) only), reflows below md, and keeps
// wide content in its own overflow-x box, so App.tsx stays content-only.
import { Children, createContext, Fragment, isValidElement, useContext, useEffect, useLayoutEffect, useRef, useState } from 'react'
import type { MouseEvent, ReactElement, ReactNode, RefObject } from 'react'
import { Highlight, themes } from 'prism-react-renderer'
import { ArrowRight, Check, Database, KeyRound, Maximize2, PanelsTopLeft, Plug, Settings2, Workflow, X, ZoomIn, ZoomOut } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { TransformComponent, TransformWrapper, useControls, useTransformEffect } from 'react-zoom-pan-pinch'
import { Bar, BarChart, CartesianGrid, Line, LineChart, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { format, getDay, parseISO } from 'date-fns'
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

type SectionProps = { id: string; title: string; group?: string; takeaway?: ReactNode; children?: ReactNode }
type TocEntry = { id: string; title: string; group: string | undefined }
type TocGroup = { group: string | undefined; entries: TocEntry[] }

const RAIL_CSS = `
.xk-rail a{display:flex;align-items:center;color:var(--ink-3);text-decoration:none;transition:color .18s;font-size:13px;line-height:1.35}
.xk-rail a>span{font-weight:600}.xk-rail a:not([data-active])>span{font-weight:400}
.xk-rail a::before{content:"";flex:0 0 auto;width:.9em;height:.9em;margin-right:.45rem;border-radius:99px;background:var(--border-hi);transform:scale(.4);transition:background .18s,transform .18s}
.xk-rail a[data-active]{color:var(--brand)}.xk-rail a[data-active]::before{background:var(--brand);transform:scale(1)}
.xk-rail .xk-group{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-3);font-weight:600;margin:.9rem 0 .35rem}
.xk-rail .xk-group:first-child{margin-top:0}
.xk-rail{scrollbar-width:thin}
.xk-prose{max-width:88ch}
.xk-anchor{display:inline-flex;align-items:center;margin-left:.5rem;font-size:.7em;color:var(--ink-3);text-decoration:none;opacity:0;transition:opacity .15s,color .15s}
.xk-heading:hover .xk-anchor,.xk-anchor:focus-visible{opacity:1}.xk-anchor:hover{color:var(--brand)}
@media (hover:none){.xk-anchor{opacity:.5}}
section[id]{scroll-margin-top:1.5rem}
.xk-shift-row{transition:background .15s}.xk-shift-row:hover>*{box-shadow:inset 0 0 0 999px color-mix(in srgb,var(--ink) 3%,transparent)}
.xk-shift-row:hover .xk-shift-label{color:var(--ink)}
.xk-stage svg{width:100%!important;height:100%!important;max-width:none!important;min-width:0!important}.xk-stage>div{overflow:visible!important}
.xk-change-row{transition:background .15s}.xk-change-row:hover{background:color-mix(in srgb,var(--ink) 3%,transparent)}`

/**
 * The whole page: theme, fonts, own scroll container, hero, side-rail TOC.
 * Put <Section>s as DIRECT children: the TOC is built from them (3+ → rail at lg).
 */
export function Page({ meta = {}, eyebrow, title, thesis, pills = [], children }: {
  meta?: Meta; eyebrow?: ReactNode; title: ReactNode; thesis: ReactNode; pills?: ReactNode[]; children?: ReactNode
}) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const railRef = useRef<HTMLElement>(null)
  const sections = collectSections(children)
  const groups = groupSections(sections)
  const rail = sections.length >= 3
  useActiveEntryInView({ scrollRef, railRef })
  useScrollToLinkedSection({ scrollRef })
  return (
    <MetaCtx.Provider value={meta}>
      <Theme />
      <link rel="stylesheet" precedence="default" href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&display=swap" />
      <style>{RAIL_CSS}</style>
      <div ref={scrollRef} className="h-screen overflow-y-auto" style={{ background: 'var(--bg)', color: 'var(--ink)', fontFamily: 'Geist, ui-sans-serif, system-ui, sans-serif' }}>
        {rail && (
          <Scrollspy targetRef={scrollRef} offset={96} history={false} className="contents">
            <nav ref={railRef} className="xk-rail fixed left-5 top-10 bottom-6 hidden lg:flex flex-col gap-2 w-48 overflow-y-auto pr-2" aria-label="Contents">
              {groups.map(({ group, entries }) => (
                <Fragment key={group ?? entries[0]?.id}>
                  {group && <p className="xk-group">{group}</p>}
                  {entries.map(s => <a key={s.id} href={`#${s.id}`} data-scrollspy-anchor={s.id}><span>{s.title}</span></a>)}
                </Fragment>
              ))}
            </nav>
          </Scrollspy>
        )}
        <main className={`w-full max-w-[1280px] 2xl:max-w-[1480px] px-4 md:px-8 pb-24 ${rail ? 'lg:pl-60' : 'mx-auto'}`}>
          <header className="pt-10 md:pt-16 pb-8 md:pb-12">
            {eyebrow && <p className="mono text-xs uppercase tracking-[0.16em] mb-3" style={{ color: 'var(--brand)' }}>{eyebrow}</p>}
            <h1 className="text-3xl md:text-5xl font-semibold tracking-tight leading-tight" style={{ color: 'var(--ink)' }}>{title}</h1>
            <p data-thesis className="xk-prose text-lg md:text-xl mt-4 leading-relaxed" style={{ color: 'var(--ink-2)' }}>{thesis}</p>
            {pills.length > 0 && <div className="flex flex-wrap gap-2 mt-5">{pills.map((p, i) => <Chip key={i}>{p}</Chip>)}</div>}
            {rail && groups.some(g => g.group) && <ContentsOverview groups={groups} />}
          </header>
          {withPartDividers(children)}
        </main>
      </div>
    </MetaCtx.Provider>
  )
}

function collectSections(children: ReactNode): TocEntry[] {
  return Children.toArray(children)
    .filter((c): c is ReactElement<SectionProps> => isValidElement(c) && c.type === Section)
    .map(c => ({ id: c.props.id, title: c.props.title, group: c.props.group }))
}

function groupSections(sections: TocEntry[]): TocGroup[] {
  return sections.reduce<TocGroup[]>((groups, entry) => {
    const last = groups.at(-1)
    if (last && last.group === entry.group) last.entries.push(entry)
    else groups.push({ group: entry.group, entries: [entry] })
    return groups
  }, [])
}

function useActiveEntryInView({ scrollRef, railRef }: {
  scrollRef: RefObject<HTMLDivElement | null>; railRef: RefObject<HTMLElement | null>
}) {
  useEffect(() => {
    const scroller = scrollRef.current
    if (!scroller) return
    const reveal = () => railRef.current?.querySelector('[data-active]')?.scrollIntoView({ block: 'nearest' })
    scroller.addEventListener('scroll', reveal, { passive: true })
    return () => scroller.removeEventListener('scroll', reveal)
  }, [scrollRef, railRef])
}

/** Grouped contents under the hero: every part with its sections, readable at any width. */
function ContentsOverview({ groups }: { groups: TocGroup[] }) {
  return (
    <nav aria-label="Parts" className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {groups.map(({ group, entries }, index) => (
        <div key={group ?? index} className="rounded-lg p-4" style={{ border: '1px solid var(--border)', background: 'var(--surface)' }}>
          <p className="mono text-xs uppercase tracking-[0.14em] mb-2" style={{ color: 'var(--brand)' }}>{`Part ${index + 1}`}{group ? ` · ${group}` : ''}</p>
          <ol className="grid gap-1 text-sm">
            {entries.map(e => <li key={e.id}><a href={`#${e.id}`} style={{ color: 'var(--ink-2)' }}>{e.title}</a></li>)}
          </ol>
        </div>
      ))}
    </nav>
  )
}

/** Inserts a part heading before the first section of each new group. */
function withPartDividers(children: ReactNode): ReactNode {
  let previous: string | undefined
  let part = 0
  return Children.toArray(children).map(child => {
    if (!isValidElement<SectionProps>(child) || child.type !== Section) return child
    const group = child.props.group
    const starts = group !== undefined && group !== previous
    previous = group
    if (!starts) return child
    part += 1
    return (
      <Fragment key={`part-${child.props.id}`}>
        <p className="mono text-xs uppercase tracking-[0.18em] pt-12 -mb-6" style={{ color: 'var(--brand)' }}>{`Part ${part} · ${group}`}</p>
        {child}
      </Fragment>
    )
  })
}

/** A top-level section. `takeaway` is the one line a skimmer must get. */
export function Section({ id, title, takeaway, children }: SectionProps) {
  return (
    <section id={id} className="py-10 md:py-14" style={{ borderTop: '1px solid var(--border)' }}>
      <h2 className="xk-heading text-2xl md:text-3xl font-semibold tracking-tight" style={{ color: 'var(--ink)' }}>
        {title}
        <SectionLink sectionId={id} />
      </h2>
      {takeaway && <p data-takeaway className="xk-prose text-base md:text-lg mt-2 font-medium" style={{ color: 'var(--ink)' }}>{takeaway}</p>}
      <div className="mt-6 grid gap-6 min-w-0">{children}</div>
    </section>
  )
}

const COPIED_FEEDBACK_MS = 1500

/** Hover "#" after a section title: puts the section in the URL and copies the link. */
function SectionLink({ sectionId }: { sectionId: string }) {
  const [copied, setCopied] = useState(false)
  const copySectionLink = async (event: MouseEvent<HTMLAnchorElement>) => {
    event.preventDefault()
    const url = new URL(window.location.href)
    url.hash = sectionId
    history.replaceState(null, '', url)
    document.getElementById(sectionId)?.scrollIntoView({ behavior: 'smooth' })
    const written = await navigator.clipboard?.writeText(url.toString()).then(() => true, () => false)
    if (!written) return
    setCopied(true)
    setTimeout(() => setCopied(false), COPIED_FEEDBACK_MS)
  }
  return (
    <a href={`#${sectionId}`} onClick={copySectionLink} data-noprose className="xk-anchor mono" aria-label="Copy link to this section">
      {copied ? <Check size={16} /> : '#'}
    </a>
  )
}

/** Scroll to the section named in the URL once the page has rendered it. */
function useScrollToLinkedSection({ scrollRef }: { scrollRef: RefObject<HTMLDivElement | null> }) {
  useEffect(() => {
    const sectionId = decodeURIComponent(window.location.hash.slice(1))
    if (!sectionId || !scrollRef.current) return
    document.getElementById(sectionId)?.scrollIntoView()
  }, [scrollRef])
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
 * First use of a new word: <Term def="a folder of related work shared by a team">project</Term>.
 * Renders the word in bold with its plain-words definition inline, once. After that, use the bare word.
 */
export function Term({ def, children }: { def: ReactNode; children: ReactNode }) {
  return <><strong data-term style={{ color: 'var(--ink)' }}>{children}</strong> <span data-noprose style={{ color: 'var(--ink-3)' }}>({def})</span></>
}

/** Inline identifier: <Id>fetchUser()</Id>. */
export function Id({ children }: { children: ReactNode }) {
  return <code className="mono px-1 py-px rounded" style={{ fontSize: 'max(12px, 0.9em)', background: 'var(--brand-soft)', color: 'var(--brand-ink)' }}>{children}</code>
}

/** Something that no longer exists, inside an example value: <Gone>Backoffice account</Gone>. */
export function Gone({ children }: { children: ReactNode }) {
  return <s data-noprose className="mono inline-block text-xs px-2 py-0.5 rounded-full whitespace-nowrap align-middle decoration-1" style={{ color: 'var(--rm)', background: 'var(--rm-soft)' }}>{children}</s>
}

/** Something new, inside an example value: <Added>staff_member row</Added>. */
export function Added({ children }: { children: ReactNode }) {
  return <span data-noprose className="mono inline-block text-xs px-2 py-0.5 rounded-full whitespace-nowrap align-middle" style={{ color: 'var(--add)', background: 'var(--add-soft)' }}>+ {children}</span>
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

type ShiftRow = { aspect: ReactNode; hint?: ReactNode; before: ReactNode; after: ReactNode; same?: boolean }
type ShiftResult = { before: ReactNode; after: ReactNode }

const BEFORE_FILL = 'color-mix(in srgb, var(--ink) 4%, transparent)'
const AFTER_FILL = 'var(--brand-soft)'
const SHIFT_COLUMNS = 'md:grid-cols-[minmax(7rem,10rem)_1fr_1fr]'
const SMALL_CAPS = 'mono text-xs uppercase tracking-[0.12em]'

/**
 * Old → new, shown on one concrete example. `example` names it ("Ido: one person, two sign-ins"),
 * each row is a short label with compact example values (ids, chips, a few words; `hint` is a small line
 * under the label, `same` marks a row that didn't change), `result` is the outcome on both sides, and `caption` is the one-sentence
 * description at the end. Free-form `before`/`after` is for mockups and screenshots.
 */
export function BeforeAfter({ example, rows, result, caption, before, after, beforeLabel = 'Before', afterLabel = 'After' }: {
  example?: ReactNode; rows?: ShiftRow[]; result?: ShiftResult; caption?: ReactNode
  before?: ReactNode; after?: ReactNode; beforeLabel?: ReactNode; afterLabel?: ReactNode
}) {
  return (
    <figure className="grid gap-3 min-w-0">
      {rows
        ? <ShiftExample example={example} rows={rows} result={result} beforeLabel={beforeLabel} afterLabel={afterLabel} />
        : <ShiftPanels before={before} after={after} beforeLabel={beforeLabel} afterLabel={afterLabel} />}
      {caption && <ShiftCaption>{caption}</ShiftCaption>}
    </figure>
  )
}

function ShiftExample({ example, rows, result, beforeLabel, afterLabel }: {
  example?: ReactNode; rows: ShiftRow[]; result?: ShiftResult; beforeLabel: ReactNode; afterLabel: ReactNode
}) {
  const [hideUnchanged, setHideUnchanged] = useState(false)
  const unchangedCount = rows.filter(row => row.same).length
  const shownRows = hideUnchanged ? rows.filter(row => !row.same) : rows
  return (
    <div className="min-w-0 rounded-xl overflow-hidden text-sm" style={{ border: '1px solid var(--border)', background: 'var(--surface)' }}>
      <ShiftHeader example={example} unchangedCount={unchangedCount} hideUnchanged={hideUnchanged} onToggle={() => setHideUnchanged(hidden => !hidden)} />
      <div className={`hidden md:grid ${SHIFT_COLUMNS}`}>
        <span />
        <ShiftColumnTitle tone="before">{beforeLabel}</ShiftColumnTitle>
        <ShiftColumnTitle tone="after">{afterLabel}</ShiftColumnTitle>
      </div>
      {shownRows.map((row, index) => (
        <ShiftLine key={index} label={row.aspect} hint={row.hint} before={row.before} after={row.after} same={row.same ?? false} beforeLabel={beforeLabel} afterLabel={afterLabel} />
      ))}
      {result && <ShiftVerdict result={result} beforeLabel={beforeLabel} afterLabel={afterLabel} />}
    </div>
  )
}

function ShiftHeader({ example, unchangedCount, hideUnchanged, onToggle }: {
  example?: ReactNode; unchangedCount: number; hideUnchanged: boolean; onToggle: () => void
}) {
  if (!example && !unchangedCount) return null
  return (
    <div className="px-4 py-2.5 flex flex-wrap items-center gap-x-3 gap-y-1.5" style={{ borderBottom: '1px solid var(--border)' }}>
      <span className={SMALL_CAPS} style={{ color: 'var(--ink-3)' }}>Example</span>
      <span className="font-medium min-w-0" style={{ color: 'var(--ink)' }}>{example}</span>
      {unchangedCount > 0 && (
        <button type="button" onClick={onToggle} aria-pressed={hideUnchanged}
          className="ml-auto text-xs px-2.5 py-1 rounded-full transition-colors"
          style={{ color: hideUnchanged ? 'var(--brand-ink)' : 'var(--ink-3)', background: hideUnchanged ? 'var(--brand-soft)' : 'transparent', border: '1px solid var(--border)' }}>
          {hideUnchanged ? `Show unchanged (${unchangedCount})` : 'Hide unchanged'}
        </button>
      )}
    </div>
  )
}

function ShiftColumnTitle({ tone, children }: { tone: 'before' | 'after'; children: ReactNode }) {
  const isAfter = tone === 'after'
  return (
    <span className="px-4 pt-3 pb-2">
      <span className={`${SMALL_CAPS} inline-block px-2 py-0.5 rounded`}
        style={{ color: isAfter ? 'var(--brand-ink)' : 'var(--ink-3)', background: isAfter ? 'var(--brand-soft)' : BEFORE_FILL }}>{children}</span>
    </span>
  )
}

function ShiftLine({ label, hint, before, after, same, beforeLabel, afterLabel }: {
  label: ReactNode; hint?: ReactNode; before: ReactNode; after: ReactNode; same: boolean; beforeLabel: ReactNode; afterLabel: ReactNode
}) {
  return (
    <div className={`xk-shift-row grid grid-cols-1 ${SHIFT_COLUMNS} min-w-0`} style={{ borderTop: '1px solid var(--border)', opacity: same ? 0.62 : 1 }}>
      <span className="xk-shift-label px-4 pt-2.5 md:py-3 min-w-0 flex flex-col justify-center" style={{ color: 'var(--ink-3)' }}>
        <span className="flex items-center gap-2">{label}{same && <span className={`${SMALL_CAPS} md:hidden`}>same</span>}</span>
        {hint && <span className="text-xs leading-snug mt-0.5" style={{ color: 'var(--ink-3)' }}>{hint}</span>}
      </span>
      <ShiftValue label={beforeLabel} fill={BEFORE_FILL} color="var(--ink-2)">{before}</ShiftValue>
      <ShiftValue label={afterLabel} fill={same ? BEFORE_FILL : AFTER_FILL} color="var(--ink)" seam={same ? 'same' : 'changed'}>{after}</ShiftValue>
    </div>
  )
}

/** The after cell carries a badge on the seam: → where the row changed, = where it didn't. */
function ShiftValue({ label, fill, color, seam, children }: { label: ReactNode; fill: string; color: string; seam?: 'same' | 'changed'; children: ReactNode }) {
  return (
    <div className="relative min-w-0 px-4 md:px-5 py-2.5 md:py-3 flex flex-wrap items-center gap-x-2 gap-y-1" style={{ background: fill, color }}>
      <span className={`md:hidden ${SMALL_CAPS} w-full`} style={{ color: 'var(--ink-3)' }}>{label}</span>
      {seam && <SeamBadge changed={seam === 'changed'} />}
      {children}
    </div>
  )
}

function SeamBadge({ changed }: { changed: boolean }) {
  return (
    <span aria-hidden className="hidden md:grid absolute left-0 top-1/2 -translate-x-1/2 -translate-y-1/2 w-5 h-5 rounded-full place-items-center text-xs leading-none"
      style={changed
        ? { background: 'var(--brand)', color: 'var(--surface)' }
        : { background: 'var(--surface)', color: 'var(--ink-3)', border: '1px solid var(--border-hi)' }}>
      {changed ? <ArrowRight size={12} strokeWidth={2.5} /> : '='}
    </span>
  )
}

function ShiftVerdict({ result, beforeLabel, afterLabel }: { result: ShiftResult; beforeLabel: ReactNode; afterLabel: ReactNode }) {
  return (
    <div className={`grid grid-cols-1 ${SHIFT_COLUMNS} min-w-0 font-semibold`} style={{ borderTop: '1px solid var(--border-hi)' }}>
      <span className="px-4 pt-3 md:py-3.5 flex items-center" style={{ color: 'var(--ink)' }}>Result</span>
      <VerdictCell label={beforeLabel} ok={false}>{result.before}</VerdictCell>
      <VerdictCell label={afterLabel} ok>{result.after}</VerdictCell>
    </div>
  )
}

function VerdictCell({ label, ok, children }: { label: ReactNode; ok: boolean; children: ReactNode }) {
  const Icon = ok ? Check : X
  const tone = ok ? 'var(--add)' : 'var(--rm)'
  return (
    <div className="min-w-0 px-4 md:px-5 py-3 md:py-3.5 flex flex-wrap items-center gap-x-2.5 gap-y-1" style={{ background: ok ? 'var(--add-soft)' : 'var(--rm-soft)', color: tone }}>
      <span className={`md:hidden ${SMALL_CAPS} w-full font-normal`} style={{ color: 'var(--ink-3)' }}>{label}</span>
      <span className="grid place-items-center w-5 h-5 rounded-full shrink-0" style={{ background: tone, color: 'var(--surface)' }}><Icon size={13} strokeWidth={3} /></span>
      <span>{children}</span>
    </div>
  )
}

function ShiftCaption({ children }: { children: ReactNode }) {
  return (
    <figcaption className="xk-prose flex gap-3 leading-relaxed pl-3" style={{ borderLeft: '3px solid var(--brand)', color: 'var(--ink-2)' }}>
      <span className={`${SMALL_CAPS} pt-1 shrink-0`} style={{ color: 'var(--brand-ink)' }}>In short</span>
      <span>{children}</span>
    </figcaption>
  )
}

function ShiftPanels({ before, after, beforeLabel, afterLabel }: { before: ReactNode; after: ReactNode; beforeLabel: ReactNode; afterLabel: ReactNode }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-3 md:gap-4 items-stretch min-w-0">
      <ShiftPanel label={beforeLabel} fill={BEFORE_FILL} labelColor="var(--ink-3)">{before}</ShiftPanel>
      <div className="hidden md:flex items-center" style={{ color: 'var(--ink-3)' }}><ArrowRight size={20} /></div>
      <ShiftPanel label={afterLabel} fill={AFTER_FILL} labelColor="var(--brand-ink)">{after}</ShiftPanel>
    </div>
  )
}

function ShiftPanel({ label, fill, labelColor, children }: { label: ReactNode; fill: string; labelColor: string; children: ReactNode }) {
  return (
    <div className="min-w-0 rounded-lg p-4 md:p-5" style={{ background: fill, border: '1px solid var(--border)' }}>
      <p className={`${SMALL_CAPS} mb-2`} style={{ color: labelColor }}>{label}</p>
      <div className="grid gap-3 min-w-0 leading-relaxed" style={{ color: 'var(--ink)' }}>{children}</div>
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

/**
 * Generic table. The first column names each row (row header); `mono` = column indexes
 * holding identifiers only (prefer <Id> inside a cell). Scrolls in its own box.
 */
export function Table({ columns, rows, mono = [] }: { columns: ReactNode[]; rows: ReactNode[][]; mono?: number[] }) {
  const monoCell = (index: number) => mono.includes(index) ? 'mono text-[13px]' : ''
  return (
    <div className="w-full min-w-0 overflow-x-auto rounded-lg" style={{ border: '1px solid var(--border)', background: 'var(--surface)' }}>
      <table className="w-full min-w-[560px] text-sm tabular-nums">
        <thead style={{ background: 'color-mix(in srgb, var(--ink) 4%, transparent)' }}>
          <tr>{columns.map((column, index) => (
            <th key={index} scope="col" className="text-left text-xs font-semibold uppercase tracking-[0.08em] px-4 py-3"
              style={{ color: 'var(--ink-3)', borderBottom: '1px solid var(--border-hi)' }}>{column}</th>
          ))}</tr>
        </thead>
        <tbody>{rows.map((row, rowIndex) => (
          <tr key={rowIndex} style={{ borderTop: rowIndex ? '1px solid var(--border)' : undefined }}>
            {row.map((cell, index) => index === 0
              ? <th key={index} scope="row" className={`text-left font-medium align-top px-4 py-3 w-[22%] ${monoCell(index)}`} style={{ color: 'var(--ink)' }}>{cell}</th>
              : <td key={index} className={`px-4 py-3 align-top leading-relaxed ${monoCell(index)}`} style={{ color: 'var(--ink-2)' }}>{cell}</td>)}
          </tr>
        ))}</tbody>
      </table>
    </div>
  )
}

type ChangeArea = 'config' | 'behavior' | 'data' | 'api' | 'ui' | 'access'
type InterfaceChange = { name: ReactNode; area?: ChangeArea; before?: ReactNode; after?: ReactNode; note?: ReactNode }
type ChangeKind = 'added' | 'removed' | 'changed'

const CHANGE_TONE = {
  added: { color: 'var(--add)', fill: 'var(--add-soft)', sign: '+' },
  removed: { color: 'var(--rm)', fill: 'var(--rm-soft)', sign: '−' },
  changed: { color: 'var(--brand-ink)', fill: 'var(--brand-soft)', sign: '~' },
} as const satisfies Record<ChangeKind, { color: string; fill: string; sign: string }>

const AREA_ICON = {
  config: Settings2, behavior: Workflow, data: Database, api: Plug, ui: PanelsTopLeft, access: KeyRound,
} as const satisfies Record<ChangeArea, LucideIcon>

/**
 * Interface changes as a compact changelog: one line per change with a status dot, the name and
 * its area, then `was → now` in a few words. Only `after` = added, only `before` = removed.
 * `note` is the one detail a reader needs (a required value, an action), shown small underneath.
 */
export function Changes({ rows }: { rows: InterfaceChange[] }) {
  return (
    <div className="grid min-w-0 rounded-xl overflow-hidden text-sm" style={{ border: '1px solid var(--border)', background: 'var(--surface)' }}>
      {rows.map((change, index) => <ChangeLine key={index} change={change} isFirst={index === 0} />)}
    </div>
  )
}

function ChangeLine({ change, isFirst }: { change: InterfaceChange; isFirst: boolean }) {
  const kind = changeKindOf(change)
  const tone = CHANGE_TONE[kind]
  return (
    <div className="xk-change-row grid grid-cols-[1.75rem_1fr] md:grid-cols-[1.75rem_minmax(11rem,16rem)_1fr] gap-x-3 gap-y-1.5 px-4 py-3 min-w-0 items-start"
      style={{ borderTop: isFirst ? undefined : '1px solid var(--border)' }}>
      <span title={kind} className="mono grid place-items-center w-6 h-6 rounded-full font-semibold" style={{ color: tone.color, background: tone.fill }}>{tone.sign}</span>
      <ChangeName change={change} kind={kind} />
      <div className="col-start-2 md:col-start-3 min-w-0 grid gap-1">
        <ChangeDiff change={change} />
        {change.note && <p className="text-xs leading-relaxed" style={{ color: 'var(--ink-3)' }}>{change.note}</p>}
      </div>
    </div>
  )
}

function ChangeName({ change, kind }: { change: InterfaceChange; kind: ChangeKind }) {
  const AreaIcon = change.area ? AREA_ICON[change.area] : undefined
  return (
    <div className="min-w-0 pt-0.5">
      <p className="font-medium break-words" style={{ color: 'var(--ink)' }}>{change.name}</p>
      <p className={`${SMALL_CAPS} flex items-center gap-1.5 mt-0.5`} style={{ color: 'var(--ink-3)' }}>
        {AreaIcon && <AreaIcon size={12} />}{change.area ?? ''}{change.area ? ' · ' : ''}{kind}
      </p>
    </div>
  )
}

function ChangeDiff({ change }: { change: InterfaceChange }) {
  return (
    <p className="flex flex-wrap items-center gap-x-2 gap-y-1 leading-relaxed pt-0.5">
      {change.before && <span style={{ color: 'var(--ink-3)' }}>{change.before}</span>}
      {change.before && change.after && <ArrowRight size={14} style={{ color: 'var(--ink-3)', flexShrink: 0 }} />}
      {change.after && <span style={{ color: 'var(--ink)' }}>{change.after}</span>}
    </p>
  )
}

function changeKindOf(change: InterfaceChange): ChangeKind {
  if (!change.before) return 'added'
  if (!change.after) return 'removed'
  return 'changed'
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

type SeriesTone = 'brand' | 'signal' | 'muted' | 'add' | 'rm' | 'ink'
type TimeSeries = { key: string; label: ReactNode; tone: SeriesTone }
type Milestone = { date: string; label: ReactNode; focal?: boolean }
type TimePoint = { date: string } & Record<string, number | string>

const TONE_VAR = { brand: '--brand', signal: '--signal', muted: '--ink-3', add: '--add', rm: '--rm', ink: '--ink-2' } as const satisfies Record<SeriesTone, string>
type ChartVar = '--brand' | '--signal' | '--ink-3' | '--add' | '--rm' | '--ink-2' | '--ink' | '--border' | '--surface'

/**
 * Values over time with the events that explain them: bars (stacked or not) or lines, one slot per
 * day, `milestones` as numbered vertical markers with a key underneath (labels never collide),
 * `shadeDays` as background bands (weekdays 0 = Sunday … 6 = Saturday, e.g. [5, 6] for Fri–Sat).
 */
export function TimeChart({ data, series, kind = 'bar', stacked = false, milestones = [], shadeDays = [], yLabel, caption }: {
  data: TimePoint[]; series: TimeSeries[]; kind?: 'bar' | 'line'; stacked?: boolean
  milestones?: Milestone[]; shadeDays?: number[]; yLabel?: string; caption?: ReactNode
}) {
  const colors = useThemeColors()
  const points = data.map((point, index) => ({ ...point, slot: index }))
  const slotOf = (date: string) => data.findIndex(point => point.date === date)
  const shadedRuns = runsOfDays({ dates: data.map(point => point.date), days: shadeDays })
  const axis = { stroke: colors['--ink-3'], fontSize: 12 }
  const chartBody = [
    ...shadedRuns.map(run => <ReferenceArea key={`shade-${run.from}`} x1={run.from - 0.5} x2={run.to + 0.5} fill={colors['--ink']} fillOpacity={0.05} stroke="none" />),
    ...milestones.map((milestone, index) => (
      <ReferenceLine key={`milestone-${index}`} x={slotOf(milestone.date)} stroke={milestone.focal ? colors['--brand'] : colors['--ink-3']} strokeDasharray="4 3"
        label={<MilestoneBadge number={index + 1} color={milestone.focal ? colors['--brand'] : colors['--ink-2']} textColor={colors['--surface']} />} />
    )),
  ]
  const xAxis = <XAxis dataKey="slot" type="number" domain={[-0.5, data.length - 0.5]} ticks={weeklyTicks(data.length)} tickFormatter={slot => shortDate(data[slot]?.date)} tickLine={false} axisLine={{ stroke: colors['--border'] }} tick={axis} />
  const yAxis = <YAxis tickLine={false} axisLine={false} tick={axis} width={36} label={yLabel ? { value: yLabel, angle: -90, position: 'insideLeft', fill: colors['--ink-3'], fontSize: 12 } : undefined} />
  const grid = <CartesianGrid vertical={false} stroke={colors['--border']} />
  const tooltip = <Tooltip cursor={{ fill: colors['--ink'], fillOpacity: 0.04 }} content={<TimeTooltip series={series} milestones={milestones} data={data} />} />
  return (
    <figure className="grid gap-3 min-w-0 rounded-xl p-3 md:p-5" style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
      <div className="h-64 md:h-80 w-full min-w-0">
        <ResponsiveContainer width="100%" height="100%">
          {kind === 'bar'
            ? <BarChart data={points} margin={{ top: 24, right: 8, bottom: 0, left: 0 }} barCategoryGap="18%">
                {grid}{xAxis}{yAxis}{tooltip}{chartBody}
                {series.map((line, index) => <Bar key={line.key} dataKey={line.key} stackId={stacked ? 'stack' : undefined} fill={colors[TONE_VAR[line.tone]]}
                  radius={!stacked || index === series.length - 1 ? [3, 3, 0, 0] : 0} isAnimationActive={false} />)}
              </BarChart>
            : <LineChart data={points} margin={{ top: 24, right: 8, bottom: 0, left: 0 }}>
                {grid}{xAxis}{yAxis}{tooltip}{chartBody}
                {series.map(line => <Line key={line.key} dataKey={line.key} stroke={colors[TONE_VAR[line.tone]]} strokeWidth={2} dot={false} isAnimationActive={false} />)}
              </LineChart>}
        </ResponsiveContainer>
      </div>
      <TimeChartKey series={series} milestones={milestones} />
      {caption && <figcaption className="text-sm leading-relaxed" style={{ color: 'var(--ink-3)' }}>{caption}</figcaption>}
    </figure>
  )
}

function MilestoneBadge({ number, color, textColor, viewBox }: { number: number; color: string; textColor: string; viewBox?: { x?: number; y?: number } }) {
  const x = viewBox?.x ?? 0
  const y = (viewBox?.y ?? 0) - 12
  return (
    <g>
      <circle cx={x} cy={y} r={9} fill={color} />
      <text x={x} y={y + 4} textAnchor="middle" fontSize={11} fontWeight={600} fill={textColor}>{number}</text>
    </g>
  )
}

function TimeChartKey({ series, milestones }: { series: TimeSeries[]; milestones: Milestone[] }) {
  return (
    <div className="grid gap-2 text-sm">
      <div className="flex flex-wrap gap-x-4 gap-y-1.5">
        {series.map(line => (
          <span key={line.key} className="inline-flex items-center gap-1.5" style={{ color: 'var(--ink-2)' }}>
            <span className="w-3 h-3 rounded-sm" style={{ background: `var(${TONE_VAR[line.tone]})` }} />{line.label}
          </span>
        ))}
      </div>
      {milestones.length > 0 && (
        <ol className="flex flex-wrap gap-x-5 gap-y-1.5">
          {milestones.map((milestone, index) => (
            <li key={index} className="inline-flex items-center gap-1.5" style={{ color: milestone.focal ? 'var(--ink)' : 'var(--ink-2)' }}>
              <span className="grid place-items-center w-[18px] h-[18px] rounded-full text-xs font-semibold" style={{ background: milestone.focal ? 'var(--brand)' : 'var(--ink-2)', color: 'var(--surface)' }}>{index + 1}</span>
              <span className="mono text-xs" style={{ color: 'var(--ink-3)' }}>{shortDate(milestone.date)}</span>
              <span>{milestone.label}</span>
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}

function TimeTooltip({ series, milestones, data, active, label }: {
  series: TimeSeries[]; milestones: Milestone[]; data: TimePoint[]; active?: boolean; label?: number
}) {
  const point = label === undefined ? undefined : data[label]
  if (!active || !point) return null
  const events = milestones.filter(milestone => milestone.date === point.date)
  return (
    <div className="rounded-md px-3 py-2 text-xs grid gap-1" style={{ background: 'var(--surface)', border: '1px solid var(--border-hi)', color: 'var(--ink)' }}>
      <span className="mono" style={{ color: 'var(--ink-3)' }}>{format(parseISO(point.date), 'EEE, MMM d')}</span>
      {series.map(line => (
        <span key={line.key} className="flex items-center gap-1.5 tabular-nums">
          <span className="w-2 h-2 rounded-sm" style={{ background: `var(${TONE_VAR[line.tone]})` }} />{line.label}: <strong>{point[line.key] ?? 0}</strong>
        </span>
      ))}
      {events.map((event, index) => <span key={index} style={{ color: 'var(--brand-ink)' }}>● {event.label}</span>)}
    </div>
  )
}

function runsOfDays({ dates, days }: { dates: string[]; days: number[] }) {
  const runs: { from: number; to: number }[] = []
  dates.forEach((date, slot) => {
    if (!days.includes(getDay(parseISO(date)))) return
    const last = runs.at(-1)
    if (last && last.to === slot - 1) last.to = slot
    else runs.push({ from: slot, to: slot })
  })
  return runs
}

function weeklyTicks(count: number) {
  const step = Math.max(1, Math.ceil(count / 10))
  return Array.from({ length: Math.ceil(count / step) }, (_, index) => index * step)
}

function shortDate(date: string | undefined) {
  return date ? format(parseISO(date), 'MMM d') : ''
}

function readChartColors(): Record<ChartVar, string> {
  const style = getComputedStyle(document.documentElement)
  const value = (name: ChartVar) => style.getPropertyValue(name).trim()
  return {
    '--brand': value('--brand'), '--signal': value('--signal'), '--ink-3': value('--ink-3'), '--add': value('--add'), '--rm': value('--rm'),
    '--ink-2': value('--ink-2'), '--ink': value('--ink'), '--border': value('--border'), '--surface': value('--surface'),
  }
}

/** Recharts takes literal colors, so read the theme vars off the page and re-read when the theme flips. */
function useThemeColors(): Record<ChartVar, string> {
  const [colors, setColors] = useState(readChartColors)
  useEffect(() => {
    const refresh = () => setColors(readChartColors())
    const scheme = window.matchMedia('(prefers-color-scheme: dark)')
    scheme.addEventListener('change', refresh)
    const observer = new MutationObserver(refresh)
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
    requestAnimationFrame(refresh)
    return () => { scheme.removeEventListener('change', refresh); observer.disconnect() }
  }, [])
  return colors
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

const FIGURE_HEIGHT_SHARE = 0.7
const MAX_ZOOM = 4

type Size = { width: number; height: number }

/**
 * Frame for a diagram or chart (SVG or HTML) with an optional caption. It is shown fitted to the
 * width and to 70% of the screen height, with a zoom bar that is always there (−, fit %, +,
 * fullscreen), ctrl/⌘ + wheel zoom, double-click to toggle fit, drag-to-pan, and Esc to leave
 * fullscreen. Plain images skip the viewer.
 */
export function Figure({ caption, children }: { caption?: ReactNode; children: ReactNode }) {
  const [expanded, setExpanded] = useState(false)
  const heightLimit = useWindowHeightShare(FIGURE_HEIGHT_SHARE)
  return (
    <figure className="min-w-0 rounded-xl p-2 md:p-4" style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
      <DiagramViewer heightLimit={heightLimit} onExpand={() => setExpanded(true)}>{children}</DiagramViewer>
      {caption && <figcaption className="text-sm mt-2 px-2" style={{ color: 'var(--ink-3)' }}>{caption}</figcaption>}
      {expanded && <FigureFullscreen caption={caption} onClose={() => setExpanded(false)}>{children}</FigureFullscreen>}
    </figure>
  )
}

/**
 * An interactive widget: `controls` (pickers, toggles, the inspector) in a column that stays in view
 * while the reader scrolls and zooms the charts beside it. Below lg the controls pin to the top.
 */
export function Playground({ controls, children }: { controls: ReactNode; children: ReactNode }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[minmax(16rem,22rem)_1fr] gap-4 lg:gap-6 items-start min-w-0">
      <aside className="grid gap-3 min-w-0 sticky top-0 z-10 max-h-[45vh] overflow-y-auto py-2 lg:py-0 lg:top-4 lg:max-h-[calc(100vh-2rem)]"
        style={{ background: 'var(--bg)' }}>
        {controls}
      </aside>
      <div className="grid gap-6 min-w-0">{children}</div>
    </div>
  )
}

function FigureFullscreen({ caption, onClose, children }: { caption?: ReactNode; onClose: () => void; children: ReactNode }) {
  const heightLimit = useWindowHeightShare(1) - FULLSCREEN_CHROME_PX
  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === 'Escape') onClose() }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [onClose])
  return (
    <div role="dialog" aria-modal className="fixed inset-0 z-50 flex flex-col gap-3 p-4 md:p-6" style={{ background: 'var(--bg)' }}>
      <div className="flex items-center gap-3 min-w-0">
        <p className="text-sm min-w-0 flex-1 truncate" style={{ color: 'var(--ink-2)' }}>{caption}</p>
        <ViewerButton label="Close (Esc)" onClick={onClose}><X size={16} /></ViewerButton>
      </div>
      <DiagramViewer heightLimit={heightLimit} fill>{children}</DiagramViewer>
    </div>
  )
}

const FULLSCREEN_CHROME_PX = 96
const FULLSCREEN_MAX_FIT = 2
// The library scales this by the wheel delta: one mouse-wheel notch (~100) zooms ~25%, a pinch tick much less.
const WHEEL_ZOOM_STEP = 0.0025

function DiagramViewer({ heightLimit, fill = false, onExpand, children }: {
  heightLimit: number; fill?: boolean; onExpand?: () => void; children: ReactNode
}) {
  const stageRef = useRef<HTMLDivElement>(null)
  const frameRef = useRef<HTMLDivElement>(null)
  const natural = useContentSize(stageRef)
  const frameWidth = useElementWidth(frameRef)
  if (!natural) return <div ref={stageRef}>{children}</div>
  const fitScale = Math.min(fill ? FULLSCREEN_MAX_FIT : 1, (frameWidth || natural.width) / natural.width, heightLimit / natural.height)
  const frameHeight = fill ? heightLimit : Math.ceil(natural.height * fitScale)
  return (
    <div ref={frameRef} className="grid gap-2 min-w-0">
      <TransformWrapper key={`${frameWidth}x${frameHeight}`} initialScale={fitScale} minScale={fitScale} maxScale={Math.max(MAX_ZOOM, fitScale)}
        centerOnInit limitToBounds centerZoomedOut
        wheel={{ activationKeys: isZoomModifierHeld, step: WHEEL_ZOOM_STEP }}
        doubleClick={{ mode: 'toggle' }} keyboard={{ disabled: false }}>
        <ViewerToolbar fitScale={fitScale} onExpand={onExpand} legend={natural.legend} />
        <TransformComponent wrapperClass="rounded-lg" wrapperStyle={{ width: '100%', height: frameHeight }}>
          <div className="xk-stage" style={{ width: natural.width, height: natural.height }}>{children}</div>
        </TransformComponent>
      </TransformWrapper>
    </div>
  )
}

/** ctrl or ⌘ (either one; a trackpad pinch arrives as ctrl) zooms; a plain wheel scrolls the page. */
function isZoomModifierHeld(keys: string[]) {
  return keys.includes('Control') || keys.includes('Meta')
}

function ViewerToolbar({ fitScale, onExpand, legend }: { fitScale: number; onExpand?: () => void; legend: SVGSVGElement | null }) {
  const { zoomIn, zoomOut, resetTransform } = useControls()
  const [scale, setScale] = useState(fitScale)
  useTransformEffect(({ state }) => setScale(state.scale))
  return (
    <div className="flex flex-wrap items-center justify-end gap-1">
      {legend && <div className="mr-auto min-w-0 max-w-full"><PinnedLegend legend={legend} /></div>}
      <ViewerButton label="Zoom out" onClick={() => zoomOut()}><ZoomOut size={16} /></ViewerButton>
      <ViewerButton label="Fit" onClick={() => resetTransform()}><span className="mono text-xs px-1 tabular-nums">{Math.round(scale * 100)}%</span></ViewerButton>
      <ViewerButton label="Zoom in" onClick={() => zoomIn()}><ZoomIn size={16} /></ViewerButton>
      {onExpand && <ViewerButton label="Fullscreen" onClick={onExpand}><Maximize2 size={16} /></ViewerButton>}
    </div>
  )
}

function ViewerButton({ label, onClick, children }: { label: string; onClick: () => void; children: ReactNode }) {
  return (
    <button type="button" title={label} aria-label={label} onClick={onClick}
      className="grid place-items-center min-w-7 h-7 px-1 rounded-md transition-colors hover:bg-[var(--brand-soft)]" style={{ color: 'var(--ink-2)', border: '1px solid var(--border)', background: 'var(--surface)' }}>
      {children}
    </button>
  )
}

type ContentSize = Size & { legend: SVGSVGElement | null }

/**
 * The natural size of the content: the first <svg>'s viewBox, else the first element's rendered box
 * (an HTML chart). A rendered diagram's legend (`<g data-legend-top>`) is lifted out: the drawing is
 * cropped above it and the legend comes back as its own small <svg>, pinned beside the zoom controls.
 */
function useContentSize(stageRef: RefObject<HTMLDivElement | null>): ContentSize | null {
  const [size, setSize] = useState<ContentSize | null>(null)
  useLayoutEffect(() => {
    const stage = stageRef.current
    const svg = stage?.querySelector('svg')
    const box = svg?.viewBox.baseVal
    if (svg && box && box.width && box.height) return setSize(liftLegend({ svg, width: box.width, height: box.height }))
    const rendered = stage?.firstElementChild?.getBoundingClientRect()
    if (rendered && rendered.width && rendered.height) setSize({ width: rendered.width, height: rendered.height, legend: null })
  }, [stageRef])
  return size
}

const SVG_NS = 'http://www.w3.org/2000/svg'
const LEGEND_GAP = 8

function liftLegend({ svg, width, height }: { svg: SVGSVGElement; width: number; height: number }): ContentSize {
  const legend = svg.querySelector<SVGGElement>('g[data-legend-top]')
  if (!legend) return { width, height, legend: null }
  const drawingHeight = Number(legend.dataset.legendTop) - LEGEND_GAP
  const pinned = document.createElementNS(SVG_NS, 'svg')
  const copy = legend.cloneNode(true)
  if (copy instanceof SVGGElement) copy.querySelector('line')?.remove()
  pinned.append(copy)
  legend.style.display = 'none'
  svg.setAttribute('viewBox', `0 0 ${width} ${drawingHeight}`)
  return { width, height: drawingHeight, legend: pinned }
}

/** Mounts the lifted legend and crops it to what it draws. */
function PinnedLegend({ legend }: { legend: SVGSVGElement }) {
  const hostRef = useRef<HTMLDivElement>(null)
  useLayoutEffect(() => {
    const host = hostRef.current
    if (!host) return
    host.append(legend)
    const drawn = legend.getBBox()
    legend.setAttribute('viewBox', `${drawn.x - 2} ${drawn.y - 2} ${drawn.width + 4} ${drawn.height + 4}`)
    legend.style.width = `${drawn.width + 4}px`
    legend.style.height = `${drawn.height + 4}px`
    legend.style.maxWidth = 'none'
    return () => legend.remove()
  }, [legend])
  return <div ref={hostRef} aria-hidden className="min-w-0 overflow-x-auto" />
}

function useElementWidth(ref: RefObject<HTMLDivElement | null>) {
  const [width, setWidth] = useState(0)
  useLayoutEffect(() => {
    const element = ref.current
    if (!element) return
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width))
    observer.observe(element)
    setWidth(element.clientWidth)
    return () => observer.disconnect()
  })
  return width
}

function useWindowHeightShare(share: number) {
  const [height, setHeight] = useState(() => window.innerHeight * share)
  useEffect(() => {
    const update = () => setHeight(window.innerHeight * share)
    window.addEventListener('resize', update)
    return () => window.removeEventListener('resize', update)
  }, [share])
  return height
}
