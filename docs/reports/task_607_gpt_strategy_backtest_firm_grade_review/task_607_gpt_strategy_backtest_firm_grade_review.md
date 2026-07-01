# Task607 GPT Strategy Backtest Firm-Grade Review

## Decision Summary

- Verdict: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Key metrics: no strategy metric changed.
- What changed: used the persistent GPT/Chrome review subagent workflow to red-team Task505/508/509/512 and converted findings into a repo-native firm-grade upgrade backlog.
- Next action: execute P0 backlog in order: T600-6 broker-truth closed-trade capture, T602-5 full exact replay 99%, Task607A exact-id review packet coverage.

## Quant Expert Report

### Data Source And Source Readiness

This task used bounded review input from existing reports only:

- Task505 diagnostic strategy report.
- Task508 cost stress report.
- Task509 walk-forward OOS report.
- Task512 backtest correctness and overfit audit.
- Task599 strategy acceptance program.
- Current operating model.

GPT/Chrome produced `review_notes` only. The source-of-truth remains repo artifacts and validation commands.

### Exact Join Keys

No joins were performed in this task. The resulting backlog requires exact lifecycle and replay IDs and explicitly forbids symbol/date/price/time fallback.

### Leakage Audit

- Inferred lifecycle matching used: no.
- Missing labels treated as negatives: no.
- Missing raw sources approximated: no.
- GPT output used as metric source: no.
- Strategy acceptance changed: no.

### Split/OOS Metrics

Existing source metrics reviewed:

| Source | Metric |
|---|---|
| Task505 | 722.99% diagnostic two-year simulated capital PnL |
| Task505 | 103 trades, 29.800% avg net, 62.1% win, 35.9% entry_reduce |
| Task508 | 663.02% after 100bp round-trip model stress |
| Task509 | 7 walk-forward folds, 89 test trades, 9.325% avg net, 56.2% win, 39.3% entry_reduce |
| Task512 | 0.687 avg degradation ratio, 3 negative/weak quarters, concentration flag, `HIGH` overfit risk |

### Failure Decomposition

The review confirms the existing failure hierarchy:

1. Broker-truth SELL lifecycle is the first fatal blocker.
2. Full exact replay 99% remains blocked by position/review completeness.
3. Exact-ID review packet coverage is incomplete.
4. Source-health durability is not yet proven.
5. Task505 has unresolved OOS degradation, quarter collapse, and concentration risk.
6. Cost stress is model-derived and not broker-truth execution cost evidence.

### Cost / Slippage Stress

Task508 is encouraging but insufficient. It proves the diagnostic strategy survives a modeled 100bp round-trip stress, not actual broker slippage, queue, partial-fill, or paper/live execution friction.

### Remaining Blockers

- `broker_truth_sell_fills=0`.
- Position replay match remains below 99% in current operating evidence.
- 20-session source health is incomplete.
- Exact-id review packet coverage is incomplete.
- Strategy remains `NOT_ACCEPTED`; real capital remains `FORBIDDEN`.

## No-Background Decision-Maker Report

The backtest is promising but not yet professional-money grade.

The 722.99% simulated result is not the decision. The decision is that the strategy still fails the gates that a serious trading desk would require before risking capital: broker-truth exits, exact replay, source health, review packets, risk controls, and OOS robustness.

We should not optimize a new alpha right now. We should first prove that the current candidate can survive professional audit. The upgrade backlog in `firm_grade_upgrade_backlog.csv` is the path.

## Artifact Manifest

See `artifact_manifest.csv`.

