# Information Architecture

## Top-Level Tabs

The fixed top-level IA is:

1. `HOME`
2. `BRAIN`
3. `PORTFOLIO`
4. `ORDERS`
5. `SYSTEM`

No other top-level trading lifecycle tab is authoritative.

## Lifecycle States

Backtest, shadow, paper, live, blocked, stale, and unknown are lifecycle or evidence states.
They appear inside screens as status, filter, evidence, or blocker fields.
They do not become top-level navigation tabs.

## Legacy Route Mapping

| Historical surface | New IA location |
| --- | --- |
| Scan | `BRAIN` candidate scanner |
| Detail | Detail route under `BRAIN`, `PORTFOLIO`, or `ORDERS` |
| Analysis | `BRAIN` thesis and validation sections |
| Market | `HOME` market context or `SYSTEM` source health |
| Risk | `SYSTEM` risk controls plus detail `Risk` section |
| Settings | `SYSTEM` |

## Required Surface Contract

Every screen that displays a decision must also display reason/thesis, evidence, source, freshness, and blocker state.

