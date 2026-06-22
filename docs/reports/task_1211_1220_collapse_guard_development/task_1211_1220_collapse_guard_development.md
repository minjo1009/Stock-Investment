# Task1211-1220 Collapse Guard Development

## Decision Summary

- Verdict: `collapse_guard_development_completed_no_replay`.
- Objective: strengthen L0-L5 against near-delisting and near-zero collapse risk without banning leverage.
- Expert packets: 3 subagent audits plus source-backed synthesis.
- Authoritative source rows: 10.
- Downloaded source files: 7.
- Evaluation-only collapse cases: 20.
- Replay executed: 0.
- Selection promoted: 0.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Core design:

- L0-L3 read survival and collapse risk.
- L4 carries thesis contradiction and risk-bucket context.
- L5 decides sell, size, holding period, and reentry rules.
- Leverage is allowed, but leveraged products route to a product-aware sleeve.

Key source families:

- Exchange listing and deficiency standards.
- Corporate actions and reverse splits.
- SEC MD&A liquidity and capital resources.
- Going concern and substantial doubt disclosures.
- Shelf, ATM, prospectus, and dilution evidence.
- Leveraged/inverse product structure and daily reset risks.

Anti-overfit boundary:

- Task1213 uses 2026Q1 collapse outcomes only as evaluation-only diagnostics.
- Future outcomes are not allowed in L0-L5 assignment logic.
- New rules must be triggered by prior-knowable source evidence.

## No-Background Decision-Maker Report

We are not adding fifty filters.

We are adding a trader brain that asks: is this candidate structurally alive, is the thesis still valid, and if risk appears, should we sell, shrink, shorten, or pause reentry?

This is design and source preparation only. It does not approve the strategy.

## Artifact Manifest

Outputs:

- `task1211_expert_roster.csv`
- `task1212_authoritative_source_catalog.csv`
- `task1213_collapse_tail_diagnostic_eval_only.csv`
- `task1214_l0_l3_survival_primitives.csv`
- `task1215_l3_relation_edges_design.csv`
- `task1216_l4_candidate_card_extensions.csv`
- `task1217_l5_trade_action_policy.csv`
- `task1218_leverage_handling_policy.csv`
- `task1219_implementation_backlog.csv`
- `task1220_collapse_guard_development_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1211_1220_collapse_guard_development_validate.py`
- `python -m unittest tests.test_trader_brain_1211_1220_collapse_guard_development`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
