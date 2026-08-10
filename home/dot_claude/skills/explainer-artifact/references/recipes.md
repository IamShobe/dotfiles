# Explainer recipes — copy-paste code

Read when building the feature. SKILL.md has the rules.

## GitHub commit-pinned permalinks

Derive both values from the checkout — don't hardcode a repo:

```bash
git rev-parse HEAD                                  # the SHA
git remote get-url origin                           # → owner/repo
```

```tsx
const REPO = 'owner/repo'   // from `git remote get-url origin`
const SHA  = 'a1b2c3d…'     // from `git rev-parse HEAD`, captured once at author time
const gh = (path: string, lines?: string) =>
  `https://github.com/${REPO}/blob/${SHA}/${path}${lines ? `#L${lines}` : ''}`
// <a href={gh('src/config/rules.yaml', '12-24')}
//    target="_blank" rel="noreferrer">rules.yaml:L12</a>
```

- Verify every `path` + line range against the actual file first (`sed -n` / open it) — a wrong line is worse than none.
- Prefer a **range** (`#L12-24`) over a bare line — single-line anchors scroll one row off in GitHub's viewport.
- Link only genuine files/lines in the change; don't invent paths to look thorough.

## Fixed side-rail TOC

Uses the vendored `Scrollspy` (`@/components/ui/scrollspy`) + own scroll container. Full scaffold + jitter-free active CSS live in **`web-artifacts-builder`'s `references/recipes.md`** (§ Scroll container + TOC scaffold) — don't duplicate. Explainer-specific: one link per top-level `<h2>`, top-level only.
