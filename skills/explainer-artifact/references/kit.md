# Explainer blocks (`import { … } from '@/explainer'`)

`@/explainer` re-exports the whole page kit from web-artifacts-builder (`$WAB/references/kit.md`: `Page`, `Section`, `Term`, `Src`, `BeforeAfter`, `Steps`, `Figure`, …) and adds two blocks for change write-ups:

| Component | Props |
|---|---|
| `<Changes rows={[{ name, before?, after?, note? }]} />` | Interface changes, old → new. Only `after` = added, only `before` = removed. |
| `<Deprecations removed={[{what, why}]} kept={[{what, why}]} />` | Gone for good vs kept as fallback. |
