# Route Map And Screen Registry

## Canonical Routes

| Route | Tab | Purpose |
| --- | --- | --- |
| `/` | `HOME` | Portfolio-level overview, DB/source status, current blockers |
| `/brain` | `BRAIN` | Candidate scanner, thesis bundles, runtime decision summaries |
| `/brain/candidates/[id]` | `BRAIN` | Candidate detail frame V2 |
| `/brain/chains/[id]` | `BRAIN` | Source-to-decision chain detail frame V2 |
| `/portfolio` | `PORTFOLIO` | Read-only positions, account summary, holdings evidence |
| `/portfolio/positions/[id]` | `PORTFOLIO` | Position detail frame V2 |
| `/orders` | `ORDERS` | Read-only order-intent, local order, broker-truth, and reconciliation views |
| `/orders/[id]` | `ORDERS` | Order detail frame V2 |
| `/system` | `SYSTEM` | Governance, source freshness, control state, validators, runtime health |
| `/system/sources` | `SYSTEM` | Source freshness and provenance |
| `/system/risk` | `SYSTEM` | Kill switch, blocker, and risk-control evidence |

## Registry Rule

Every new screen must declare:

- owning tab
- source read model
- required freshness fields
- required blocker fields
- disabled action controls, if any
- screenshot QA target
- Storybook story target, if componentized

