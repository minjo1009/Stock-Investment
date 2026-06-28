# Strategy Acceptance Contract

Last updated: 2026-06-03

## Scope

This contract defines the path from `NOT_ACCEPTED` to `ACCEPTANCE_REVIEW`.

It does not approve strategy acceptance. It defines the evidence required before a strategy acceptance review can begin.

Current state:

| Field | Status |
|---|---|
| Paper operation | `READY_FOR_CONTROLLED_PAPER_RUN` |
| Strategy acceptance | `NOT_ACCEPTED` |
| Target gate | `ACCEPTANCE_REVIEW` |
| Deployment readiness | `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY` |
| Real capital | `FORBIDDEN` |

## Source Of Truth

The readiness state is governed by `docs/ownership/readiness_registry.yaml`.

Validation command:

```powershell
python validate_readiness_registry.py
```

## Executive Priority Order

| Priority | Workstream | Owner | Gate |
|---|---|---|---|
| P0 | Exit Lifecycle | 주은 | SELL fills exist and realized lifecycle is populated |
| P0 | Candidate Funnel | 성원 | Candidates are ranked, explainable, cooled down, and audited |
| P0 | Exact Replay | 동승 | Runtime decisions, orders, fills, and positions replay with 99%+ match |
| P1 | Source Health Ledger | 윤헌 | 20 sessions pass source quality thresholds |
| P1 | Readiness Dashboard | 규승 | 필수 can diagnose state in five seconds without CSVs |
| P2 | Governance Enforcement | 중훈 | Closeout cannot pass with stale operating docs |
| P2 | Exact-ID Review Packet | 종찬 | 100% fill review packet coverage and top skipped candidate coverage |
| P2 | Slack Policy Lock | 서연 | Slack sends only allowed event classes |
| P2 | Deployment Gate Separation | 필수 | Deployment claims remain blocked until deployment contract passes |

## Acceptance Review Entry Conditions

Strategy acceptance review cannot begin until all conditions pass:

| Gate | Required Evidence |
|---|---|
| SELL fills exist | Paper mode has SELL fills from exact broker-truth lifecycle, not inferred exits |
| 100+ realized trades exist | Closed trades have realized PnL populated through `position_lifecycle` |
| Replay match >99% | decision, order, fill, and position match rates are each at least 99% |
| Source health validated | 20 trading sessions satisfy source health thresholds |
| Candidate funnel audited | Candidate generation, ranking, eligibility, skip, order, fill, and close states are auditable |
| Kill switch tested | kill-switch event path is tested and reported |
| Review packet coverage 100% | all fills and top skipped candidates have exact-id review packets |

If any item is missing, strategy acceptance remains `NOT_ACCEPTED`.

No exceptions.

## Forbidden Claims

Until SELL lifecycle and realized closed-trade evidence pass, these phrases are forbidden in reports, Slack messages, frontend copy, and final responses:

- strategy validated
- profitable strategy
- deployment ready
- production ready

Allowed language:

- controlled paper operation
- diagnostic-only
- readiness blocker
- acceptance review not started
- deployment blocked

## Required Evidence Tables

| Table | Owner | Purpose |
|---|---|---|
| `position_lifecycle` | 주은 | Entry-to-exit realized lifecycle |
| `candidate_funnel_events` | 성원 | Candidate generation through close funnel |
| `source_health_ledger` | 윤헌 | Session source quality and freshness |
| `replay_diff` | 동승 | Exact replay mismatch explanation |
| `readiness_registry.yaml` | 필수 / 중훈 | Program state and blocker ownership |

## Closeout

Every task that changes readiness must update:

- `docs/ownership/readiness_registry.yaml`
- `docs/ownership/current_operating_model.md`
- `tasks/task_registry.csv` when active/canonical state changes
- relevant task report and artifact manifest

Minimum validation:

```powershell
python validate_readiness_registry.py
python scripts/operating_closeout_validate.py
python scripts/governance_completion_audit.py
```
