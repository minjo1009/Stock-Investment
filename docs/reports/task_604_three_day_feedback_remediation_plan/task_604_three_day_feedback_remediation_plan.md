# Task604 - Three-Day Feedback Remediation Plan

## Decision Summary

- Verdict: `PRIMARY_PASS` for remediation planning and operating handoff.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Objective: convert the latest three daily feedback reports into a durable team-owned remediation board instead of another one-off critique.
- Evidence reviewed: `docs/reports/daily_feedback_2026-06-03/daily_feedback_2026-06-03.md`, `docs/reports/daily_feedback_2026-06-04/daily_feedback_2026-06-04.md`, `docs/reports/daily_feedback_2026-06-06/daily_feedback_2026-06-06.md`, `docs/ownership/team_charter.md`, `docs/ownership/current_operating_model.md`, `docs/ownership/module_ownership_map.md`, `docs/ownership/readiness_registry.yaml`, Task598, and Task599.
- Key metrics still blocking acceptance: `broker_truth_sell_fills=0`, `STOP=0`, `TP=0`, `position_match_rate=0.958333`, source-health ledger incomplete, exact-id review packet incomplete.
- What changed: this task creates a cross-team remediation board, a blocker dependency chain, and a daily closeout checklist that each team lead must use before claiming progress.
- Next action: execute the P0 chain in order: broker-truth SELL closeout, ATR/source snapshot closure, closed candidate linkage, replay position 99%, then P1/P2 visibility and governance gates.

## Quant Expert Report

### Goal Intake Contract

| Field | Fixed Value |
|---|---|
| Objective | Make the latest three daily feedback findings operational, owned, validated, and reusable. |
| Target Metrics | `broker_truth_sell_fills > 0`, exact closed lifecycle rows, `position_match_rate >= 0.99`, 20-session source health ledger, 100% fill and top-skipped exact-id review packet coverage, blocker state changed or explicitly unchanged daily. |
| Forbidden Actions | No new alpha experiments before P0 closeout; no inferred lifecycle matching; no symbol/date/price/time proximity fallback; no missing label as negative; no Slack/UI/PnL proxy as strategy acceptance; no deployment claim. |
| Available Raw Sources | Current `trading.db`, Task589 EOD artifacts, Task600-4, Task600-5, Task601-4, Task602-4, Task603-6, readiness registry, task registry. |
| Missing Raw Sources | Actual paper broker/order-status SELL fills, ATR-at-entry runtime source snapshots, complete 20-session source-health ledger, kill-switch evidence, exact-id review packets. |
| Owner Team | Research Governance for program control. |
| Reviewer Team | General Coordination / Regime Research for acceptance language; Execution & Risk for first P0 blocker. |
| Output Directory | `docs/reports/task_604_three_day_feedback_remediation_plan/` |
| Large Artifact Directory | Not applicable. No large panel was generated. |
| Validation | `python validate_readiness_registry.py`, `python scripts/task_registry_validate.py`, and closeout governance validators. |

### Three-Day Feedback Pattern

The feedback is consistent across 2026-06-03, 2026-06-04, and 2026-06-06:

1. Operational improvements are being mistaken for acceptance progress. `READY_FOR_CONTROLLED_PAPER_RUN`, Slack `SENT`, concentration improvement, and replay order recovery are useful but do not change `NOT_ACCEPTED`.
2. The first acceptance blocker is still broker-truth exit lifecycle. Runtime synthetic SELL rows do not satisfy broker truth.
3. STOP/TP validation is currently a source failure, not a risk-model pass. ATR-at-entry coverage is missing.
4. Candidate quality cannot be accepted until candidates are traced through `generated -> ranked -> ordered -> filled -> closed`.
5. Replay reporting needs to separate own replay gaps from upstream execution/source gaps.
6. Data freshness must become a 20-session ledger, not a same-day freshness assertion.
7. Dashboard, Slack, chart review, and governance must surface blocker-first truth and evidence staleness before any positive operational metric.

### Team Remediation Direction

The detailed board is `team_remediation_board.csv`. The operating order is:

1. Regime / Overall Strategy Lead locks the daily headline to `status / first blocker / stale-or-fresh evidence`.
2. Execution & Risk produces broker-truth SELL exact closeout evidence. Nothing downstream can promote without this.
3. Data & Market Microstructure closes ATR-at-entry and source-health ledger requirements.
4. Candidate Funnel and Chart Evidence attach closed lifecycle and exact-id review evidence to candidate quality.
5. Replay & Simulation reruns replay with own-gap versus upstream-gap split and reaches the 99% position gate.
6. Frontend, Slack, and Governance make blocker state visible, non-promotional, and stale-aware.

### Data Integrity Gate

- Inferred lifecycle matching used: no.
- Symbol/date/price/time proximity fallback used: no.
- Missing labels treated as negatives: no.
- Missing raw sources approximated: no.
- Labels or future outcomes used in assignment logic: no new assignment logic was created.
- Deployment-ready claim: no. The correct state remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.

### Closeout Standard For Future Daily Feedback

Every daily feedback closeout must include one of these two outcomes for every blocker:

- `status changed`, with artifact and validation command.
- `unchanged with explicit reason`, with blocker age and next validation run.

If neither is true, the day closes as an operating failure even if Slack, UI, or paper runtime improved.

## No-Background Decision-Maker Report

The last three feedback reports say the same thing: the project is running better, but the strategy is not accepted. The team keeps finding useful operating improvements, yet the hard blockers remain: no broker-truth SELL evidence, no STOP/TP proof, replay position match below 99%, incomplete source ledger, and incomplete exact-id review packets.

So the remedy is not another strategy experiment. The remedy is a fixed closeout chain. First prove real broker-truth exits. Then prove source snapshots and closed candidate linkage. Then rerun replay to the 99% gate. Only after that should dashboard, Slack, and review packets be used to support acceptance review.

Current status remains `NOT_ACCEPTED`. Real capital remains forbidden. This plan changes the operating discipline, not the acceptance state.

## Artifact Manifest

Generated by `scripts/task_artifact_manifest.py`.
