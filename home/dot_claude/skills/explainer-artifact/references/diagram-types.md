# Choosing the diagram

Pick the diagram from **the question the section answers**, not from habit.
Architecture is the right answer only when the question is "where does it sit?".
diagram-design has 41 types. ⚙ = rendered from a JSON spec (`render.py --example <type>`);
✎ = drawn by hand from `$DIAGRAM_DESIGN/references/type-<type>.md` + `diagram-brief.md`.

## By story beat

| The section answers… | Use | |
|---|---|---|
| Where does the new piece sit? What talks to what? | architecture | ⚙ |
| What happens, in order, when a request comes in? Who calls whom? | **sequence** | ⚙ |
| What statuses can X be in, and what moves it between them? | **state** | ⚙ |
| Which branch runs when? (validation, retry, fallback, routing) | flowchart | ⚙ |
| Who owns each step, and where are the handoffs? | swimlane | ⚙ |
| What changed in the data model? | er (concepts) · **db-schema** (tables, FKs, cascades) | ⚙ |
| What changed in the class/interface structure? | uml-class | ⚙ |
| What depends on what? Did we add or break a cycle? | dependency | ⚙ |
| How was the module/package tree reorganised? | tree | ⚙ |
| Who owns / gets paged / approves now? | org-chart | ⚙ |
| Where does it run? Pods, replicas, zones, versions | deployment | ⚙ |
| Which layer does the change live in? A new layer inserted? | layers | ⚙ |
| What's the blast radius or scope of the change? | nested | ⚙ |
| When does each phase happen? Deprecation schedule, incident | timeline | ⚙ |
| What's the migration/rollout plan, with overlap? | gantt | ⚙ |
| Did it get faster or smaller? Per endpoint/package, before → after | **dumbbell** (few rows) · **slopegraph** (many) | ⚙ |
| Where did the time/bytes go? A budget from start to end | **waterfall** | ⚙ |
| One number per thing (bundle per package, tests per suite) | bar | ⚙ |
| Where is the hotspot? (failures by service × week) | heatmap | ⚙ |
| What should we do next? (impact × effort) | quadrant | ⚙ |
| Test pyramid shift, or a filtering funnel with counts | pyramid | ⚙ |
| What did we investigate, and which cause was it? (bugfix/incident) | fishbone | ✎ |
| How does the quantity split and merge? (CI minutes, traffic) | sankey | ✎ |
| What did the messy "before" look like? (modernisation motivation) | it-state | ✎ |
| A feedback/reconcile loop with shared state | loop | ✎ |
| How does the developer/user experience feel across steps? | journey | ✎ |
| What ships now vs later? (MVP cut) | story-map | ✎ |
| Who can read/write what, per role? (RBAC change) | dp-security-matrix | ✎ |
| Build vs buy, a component moving toward commodity | wardley | ✎ |
| Trends over time (latency across releases) | line | ✎ |
| Two variables per item (size vs TTI per route) | scatter | ✎ |
| Part of a whole where size is the story (bundle by package) | treemap | ✎ |
| Old and new implementation overlap during a migration | venn | ✎ |
| Data-platform topology: phases, tiers, integrations | high-level · medallion · dp-integration · data-flow · process | ✎ |
| Work-in-progress census of a multi-PR migration | kanban | ✎ |
| Two similar requests, different outcomes: where they diverge | flowchart, paired-trace pattern | ✎ |

## Rules

- **Variety follows content.** If a page has two diagrams of the same type, check that both questions really are "where does it sit?". A change with a request path and a status change gets **sequence + state**, not two architectures.
- **Pairs tell a before → after story.** it-state → architecture (modernisation). Two dumbbells don't beat one. For a behaviour change, one sequence with an `alt` fragment for the new branch beats two sequences.
- **A table beats a diagram** when three columns say the same thing.
- **Budgets are hard.** Over budget → split into overview + detail, or cut. The renderer rejects over-budget specs with the reason.
- **Vocabulary**: labels use the page's words. A diagram never introduces a term the prose hasn't.

## Semantic patterns (behaviour first, then layout)

When the *behaviour* is the story, pick the pattern, then draw it with the nearest type (✎, from `$DIAGRAM_DESIGN/references/semantic-patterns.md`):

| Pattern | Trigger | Draw as |
|---|---|---|
| Fan-in queue / bottleneck | many producers → one constrained service; backpressure | data-flow |
| Lifecycle phase map | one subject through phases, waits, retries, terminals | state |
| Paired policy traces | two requests, one passes, one fails: first divergence | flowchart |
| Secure paved road | trust zones, allowed vs forbidden ingress/deploy paths | architecture |
| Governance / control catalog | controls grouped by where they're enforced | layers |
| Compensating security layers | each defence covers the previous gap; residual risk | layers |
| Traceable block decomposition | stable IDs per block, traced to code | tree |
| Stage framework with slots | stages repeat Question / Input / Output slots | process |
| Unstructured → structured artifact | chat/notes become a ticket or schema | data-flow |
