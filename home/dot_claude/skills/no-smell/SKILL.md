---
name: no-smell
description: The user's code standards, distilled from ~200 of their own PR review comments. Use before writing, editing, refactoring or reviewing any TypeScript or Python, and before saying "done" or opening a PR — even for small changes and even when the user doesn't mention style. Covers ts-pattern exhaustive matching (never switch), strict zod/pydantic parsing, object (kwargs) params, story-first function layout, using libraries instead of hand-rolled code, and explicit error handling. Also use when the user says "clean it up", "future proof", "strongly typed", "smell", "bloated" or "too manual".
---

# No Smell

Every rule here is something the user had to write in their own PR more than
once. Each repeat costs them a review round, so treat these as requirements
rather than preferences. The top three account for most of the comments:
ts-pattern, strict typing, readable structure.

## 1. Branch on kinds with ts-pattern `.exhaustive()`

When a union, enum, status, `kind`/`type` field or result tag gains a new
variant, the build must fail at every place that branches on it. `switch`,
`if/else if` chains on one field, and nested ternaries fail silently, so use:

```ts
import { match } from 'ts-pattern';

const badge = match(order.status)
  .with('pending', 'processing', () => ({ tone: 'info', label: 'In progress' }))
  .with('failed', () => ({ tone: 'danger', label: 'Failed' }))
  .with('shipped', () => ({ tone: 'success', label: 'Shipped' }))
  .exhaustive();
```

- Don't use `switch` even with a `never` default. The user wants ts-pattern
  specifically, for consistency.
- `.otherwise()` only when the input is truly open-ended (an arbitrary string).
  Leave a one-line comment saying why.
- A constant lookup is fine as `{...} satisfies Record<Status, V>`. Use `cva`
  for class variants.
- A single guard (`if (!user) return`) is not branching on kinds and is fine.
- Python: `match` + `assert_never` in the fallthrough, not `elif` chains.

## 2. Parse at the boundary: strict, once, with zod/pydantic

Untyped data that leaks inward is what made the user write "strongly type it"
and "safe_parse everywhere" again and again.

- Parse every external input (HTTP, env, JSON, files, JWT claims, queue
  messages, CLI args) with zod `safeParse` and handle the failure branch. In
  Python, use pydantic `model_validate` / `model_validate_json`.
- Use one schema for the whole payload. Don't run four sequential parses.
- Don't use `any`, don't use `as` casts to quiet the compiler, and don't use
  `JSON.parse(x) as T`. `unknown` is fine only right before a parse.
- Keep required fields required. Don't add `.optional()` to dodge an error.
- Zod object modes: `z.object` strips unknown keys, `z.strictObject` rejects
  them, and `z.looseObject` keeps them. Use loose only for third-party payloads.
- Reshape in the schema with `.transform` so callers receive the domain shape:

```ts
const webhookSchema = z
  .object({ customer_id: z.string(), amount_cents: z.number().int(), is_test: z.boolean() })
  .transform((w) => ({ customerId: w.customer_id, amountCents: w.amount_cents, isTest: w.is_test }));
```

- Derive types instead of re-listing fields: `z.infer`, `Pick`/`Omit`, and
  Remeda (`R.pick`, `R.omit`, `R.mapValues`, `R.groupBy`) instead of
  `Object.entries`, which loses types.
- `startsWith`, `split('-')[1]` or a regex on an ID means the data model is
  wrong. Carry a typed field, or return it from the server. Fix the model;
  don't patch the call site.

## 3. Layout: the module reads as a story

The user reads code top-down and wants to stop as soon as they understand.
"Super hard to read", "bloated" and "UGLY" all came from violating this.

- Put the exported entry point first. Its body is a few named steps (~15
  lines max) that read like a summary of the feature.
- Put helpers below it, in the order they're called. Each helper works at one
  level of abstraction, and you keep drilling down until the leaves are trivial.
- Prefer plain functions and data. Use a class only for real lifecycle state.
- Make names say what and on which thing: `reserveInventoryForOrder`, not `reserve`;
  `confirmPaymentCapture`, not `confirm`.
- Don't use magic numbers. Use named constants or config (values files or
  configmaps, wherever the repo already keeps config).

```ts
export async function refundOrder({ orderId, reason }: RefundOrderInput) {
  const order = await loadOrderOrFail({ orderId });
  const refund = buildRefund({ order, reason });
  await assertNotAlreadyRefunded({ orderId: order.id });
  return submitRefund({ refund });
}

async function loadOrderOrFail({ orderId }: { orderId: OrderId }) { /* ... */ }
```

## 4. Params: one destructured object (kwargs style)

`createLease(id, 3000, true)` is unreadable at the call site. A function you
define with 2+ params takes `{ customerId, ttlMs, owner }`. Callbacks whose
signature a library dictates (`.map`, `.with`, event handlers) are exempt.
Python: keyword-only (`def f(*, customer_id: str, ttl_s: int)`).

## 5. Reach for a library or a repo helper before hand-rolling

"Isn't there a popular lib for this?" and "don't we have something to reuse?"
were asked repeatedly. Search the repo first, then use these:

| Need | Use |
|---|---|
| Branching | `ts-pattern` |
| Validation | `zod` / `pydantic` |
| Typed collection/object ops | `remeda` |
| Dates, durations | `date-fns` |
| Style variants | `cva` |
| UI | `shadcn/ui` components and composites |
| Forms | `@tanstack/react-form` |
| Hooks (intervals, etc.) | `react-use`, not ad-hoc `useEffect` |
| Python CLI | `typer` |
| Cleanup | `await using` / `finally` |

## 6. Make failure explicit

- No hidden throws. Put failure in the return type (see `never-throw-typescript`).
- `Promise.all` rejects on the first failure. Pick deliberately between
  all-or-nothing and `allSettled` with per-item handling, and say which.
- Release resources on every path. Don't share mutable state across concurrent
  requests. Stream when the input size is unbounded.

## 7. Generic, minimal

- Don't write per-type or per-customer copies. Write one thing parametrized by
  the type.
- For infra and config, make the smallest change that works: narrow ingress,
  no unused resources, no knobs nobody asked for. Check that the access or
  config doesn't already exist before you add it.

## Enforcement

A PostToolUse hook runs `scripts/hook.sh` after every Edit/Write of a TS or
Python file. It reports only smells the edit **introduced** (lines already in
HEAD are ignored), and the report comes back to you as feedback. When one
arrives, fix it right away, or mark a deliberate exception on that line with
`// no-smell: <reason>` (`# no-smell:` in Python). That comment is also how
you silence the branch scan below.

## Before saying "done" / opening a PR

Run the branch-wide scan from the repo root. It covers committed, staged,
unstaged and untracked changes against the merge-base:

```bash
bash ~/.claude/skills/no-smell/scripts/check.sh            # or: check.sh <base-ref> | check.sh -- <files>
```

`== SMELL` lines fail the scan; fix each one or justify it with `no-smell:`.
`-- review` lines (new classes, ids parsed with string methods) need a look,
because only you can tell whether this repo owns that format or pattern. Then
check what regex can't: the entry point reads as a story, names are specific,
nothing is hand-rolled that a library or repo helper already does, and every
`Promise.all` choice is deliberate.

If you change `check.sh`, run `bash ~/.claude/skills/no-smell/tests/run.sh`.
