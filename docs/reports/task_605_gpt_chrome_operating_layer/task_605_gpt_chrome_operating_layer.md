# Task605 GPT/Chrome Operating Layer

## Decision Summary

- Verdict: adopt GPT/Chrome as a bounded review and ideation layer, not as a source of truth.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Key metrics: no trading metrics changed; this is an operating decision report.
- What changed: team-lead consensus and priority rules for using Chrome-controlled GPT conversations were documented.
- Next action: use GPT/Chrome first for blocker-first review, exact-lifecycle/backtest wording audit, and frontend five-second human review.

## Quant Expert Report

### Source Status

Current truth remains in repository artifacts, not in GPT conversation:

- `docs/ownership/current_operating_model.md`
- `docs/ownership/team_charter.md`
- `tasks/task_registry.csv`
- `docs/ownership/readiness_registry.yaml`
- raw/runtime market sources
- broker/order/fill/lifecycle/replay artifacts
- validation command output

GPT/Chrome output is classified as `review_notes` or `ideation_notes` only.

### Team Consensus

| Lead / Team | Verdict | Highest-Value Use |
|---|---|---|
| Data & Market Microstructure | Review layer only | Source-health ledger checklist, quote/status/LULD/depth gap review |
| Regime Research | Review layer first | Acceptance-claim red-team review before any strategy development |
| Intraday Continuation Research | Review layer first | Archetype/funnel wording audit without invented evidence |
| Backtest & Simulation Infra | Review layer first | Exact lifecycle, replay gap, split/OOS, leakage, cost/slippage audit |
| Execution & Risk | Review layer only | Broker-truth SELL, proxy PnL, runtime synthetic SELL misstatement detection |
| Frontend/UI | Review accelerator | Chrome-based five-second blocker visibility and mobile/desktop UI review |
| Research Governance | Governed adoption | Registry/report/manifest discipline and no untracked decisions |
| Slack/EOD | Review layer | Blocker-first EOD wording, duplicate/noise guardrail review |
| Chart Evidence | Review layer | Exact-id screenshot packet visibility and fake-marker prevention |

### Priority Matrix

| Priority | Use | Scope | Rule |
|---|---|---|---|
| P0 | Acceptance red-team review | Strategy/backtest/report language | Find overclaims; do not change status |
| P0 | Broker/replay blocker review | T600/T602-style lifecycle evidence | Check exact IDs and broker-truth wording only |
| P0 | Frontend five-second review | Trader Terminal dashboard and review packets | Chrome/screenshot review must show blocker first |
| P0 | Slack/EOD blocker-first review | Daily closeout and feedback loop | Status, first blocker, freshness before positive metrics |
| P1 | Backtest result development | Failure taxonomy, replay diff questions, validation checklist | Ideas must map back to artifacts and tests |
| P1 | Report standard review | Decision Summary, Quant Expert Report, No-Background Report, Manifest | Improve clarity without changing truth |
| P1 | Chart/screenshot packet QA | OHLC/VWAP/entry marker presentation | Markers require exact-id catalog/source evidence |
| P2 | Strategy ideation | New hypotheses, factor questions, failure slices | Allowed only after P0 blockers are not bypassed |
| P2 | UI polish | Layout, copy, visual hierarchy | Cannot affect acceptance status |

### Forbidden Uses

- Do not use GPT/Chrome as source-of-truth for market data, quotes, status, LULD, depth, broker fills, labels, lifecycle links, replay match, PnL, or readiness.
- Do not let GPT propose or approve symbol/date/price/time proximity fallback matching.
- Do not treat missing labels as negatives.
- Do not approximate missing raw sources with GPT inference.
- Do not treat Slack success, UI polish, Chrome screenshot success, or Graphify output as strategy acceptance.
- Do not run new alpha experiments before current P0 blocker discipline allows them.
- Do not let GPT-generated strategy ideas enter implementation without owner team, raw-source availability, artifact path, and validation command.

### Operating Cadence

Use GPT/Chrome selectively:

- P0 required: before claiming any strategy/backtest/replay/blocker status change.
- P1 optional: before publishing a material report, frontend review packet, or EOD closeout.
- P2 occasional: for ideation after the active blocker chain is not being bypassed.

Avoid daily broad re-review of every file, CSV, or dashboard. That would slow the project and create inconsistent non-reproducible opinions.

### Leakage / Matching Audit

This report makes no strategy metric claim and creates no labels. The operating rules preserve:

- no inferred lifecycle matching
- no symbol/date/price/time fallback
- no missing label to negative conversion
- no unavailable raw source approximation
- no deployment claim from diagnostic-only evidence

## No-Background Decision-Maker Report

We should use Codex-controlled Chrome/GPT, but only in a bounded way.

The best use is not "ask GPT if the strategy is good." The best use is to make GPT act like a skeptical reviewer: find overclaims, missing evidence, confusing UI, unclear backtest language, and reports that accidentally sound deployment-ready.

The immediate best uses are:

1. Strategy evaluation and development: P0 as an acceptance red-team reviewer; P2 for new ideas only after blocker discipline is respected.
2. Backtest evaluation and development: P0/P1 as a replay, leakage, split/OOS, cost/slippage, and exact-lifecycle report reviewer.
3. Frontend UI/UX evaluation and development: P0 for Chrome-based five-second blocker visibility review, especially `NOT_ACCEPTED`, first blocker, owner, freshness, and proxy-vs-realized separation.

This does not change capital readiness. Real capital remains forbidden until repository evidence and validation gates say otherwise.

## Artifact Manifest

See `artifact_manifest.csv`.

