# GitHub Project Operating Model

## Project Fields

| Field | Type | Values |
|---|---|---|
| Task ID | Text | Task489, Task493, etc. |
| Owner Team | Single select | Data, Regime, Intraday, Backtest, Execution, Governance |
| Status | Single select | Backlog, Design, Implementation, Validation, Review, Accepted, Diagnostic Only, Superseded, Archived |
| Canonical State | Single select | canonical, active, diagnostic, superseded, archived |
| Data Readiness | Single select | raw-ready, partial-source, missing-source, live-ready |
| Strategy Acceptance | Single select | not-applicable, diagnostic-only, candidate, accepted, deployment-ready |
| Priority | Single select | P0, P1, P2, P3 |
| Review Required | Multi select | Data, Regime, Intraday, Backtest, Execution, Governance |

## Views

- Executive Board: accepted, candidate, blocked, next action
- Research Pipeline: hypothesis through validation
- Data Integrity Board: raw source and leakage issues
- Team Workload: grouped by owner team
- Archive: superseded and archived tasks

## Automation Rules

- New issue with `research` label enters `Design`.
- PR touching `src/data` requests Data & Market Microstructure review.
- PR touching `src/backtest/core` requests Backtest & Simulation Infra review.
- PR touching `docs/reports` or `tasks/task_registry.csv` requests Research Governance review.
- A task cannot move to `Accepted` without registry row, report, decision CSV, and validation command.
