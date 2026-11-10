// Explainer blocks on top of the page kit. build.sh copies this file to
// src/explainer/index.tsx, so App.tsx imports everything from '@/explainer'.
import type { ReactNode } from 'react'
import { Card, Chip, Table } from '@/kit'

export * from '@/kit'

type InterfaceChange = { name: ReactNode; before?: ReactNode; after?: ReactNode; note?: ReactNode }
type ChangeKind = 'added' | 'removed' | 'changed'

const CHIP_KIND = { added: 'add', removed: 'rm', changed: 'change' } as const satisfies Record<ChangeKind, string>

/**
 * Interface changes, one block per thing that changed: its name and status first,
 * then what it was and what it is now. Only `after` = added, only `before` = removed.
 */
export function Changes({ rows }: { rows: InterfaceChange[] }) {
  return (
    <div className="grid min-w-0 rounded-lg overflow-hidden" style={{ border: '1px solid var(--border)', background: 'var(--surface)' }}>
      {rows.map((change, index) => <ChangeBlock key={index} change={change} isFirst={index === 0} />)}
    </div>
  )
}

function ChangeBlock({ change, isFirst }: { change: InterfaceChange; isFirst: boolean }) {
  const kind = changeKindOf(change)
  return (
    <div className="grid gap-2.5 p-4 md:px-5 min-w-0" style={{ borderTop: isFirst ? undefined : '1px solid var(--border)' }}>
      <p className="flex flex-wrap items-center gap-x-2.5 gap-y-1 font-medium" style={{ color: 'var(--ink)' }}>
        <Chip kind={CHIP_KIND[kind]}>{kind}</Chip>
        <span className="min-w-0">{change.name}</span>
      </p>
      <dl className="grid grid-cols-[3.25rem_1fr] gap-x-3 gap-y-1.5 min-w-0 leading-relaxed">
        {change.before && <ChangeLine label="Was" color="var(--ink-3)">{change.before}</ChangeLine>}
        {change.after && <ChangeLine label="Now" color="var(--ink)">{change.after}</ChangeLine>}
      </dl>
      {change.note && <p className="text-sm" style={{ color: 'var(--ink-3)' }}>{change.note}</p>}
    </div>
  )
}

function changeKindOf(change: InterfaceChange): ChangeKind {
  if (!change.before) return 'added'
  if (!change.after) return 'removed'
  return 'changed'
}

function ChangeLine({ label, color, children }: { label: string; color: string; children: ReactNode }) {
  return <>
    <dt className="mono text-xs uppercase tracking-[0.12em] pt-1" style={{ color: 'var(--ink-3)' }}>{label}</dt>
    <dd className="min-w-0" style={{ color }}>{children}</dd>
  </>
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
