# Task2511-2520 KIS MDD Decomposition

## Decision Summary

- Verdict: `kis_mdd_gate_failure_is_incremental_cost_drag_on_top_of_loss_cluster`.
- Base MDD: -0.28210924.
- KIS MDD: -0.30814728.
- MDD delta vs base: -0.02603804.
- KIS MDD window: 2022-01-31T21:00:00+00:00 -> 2022-08-31T21:00:00+00:00.
- MDD window trades: 14.
- Negative trades in window: 11.
- Window Task2381 PnL: -594.4978.
- Window KIS PnL: -631.106791.
- MDD window KIS cost: 61.798787.
- Gate failure primary cause: `incremental_kis_cost_drag`.
- Economic loss primary cause: `underlying_drawdown_window_trade_losses`.
- Strategy tuning performed: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Failure taxonomy:

- `broker_cost_drag`: MDD window cost/PnL delta vs Task2381 = -36.608991. Repair: cost-aware MDD guard should avoid thin-margin trades during existing drawdown windows.
- `negative_trade_concentration`: Negative trades in KIS MDD window = 11, aggregate KIS PnL = -814.112543. Repair: diagnose pre-entry and reduce/exit logic for the small set of window loss contributors.
- `symbol_specific_loss_cluster`: Worst symbols by KIS PnL: CC=-278.567104;AVGO=-139.123901;CBT=-100.221771;AME=-71.609492;ADM=-58.66196 Repair: audit whether losers shared runtime_action, volatility_cause, or weak winner_defense_bucket before proposing guards.

Worst KIS MDD-window trades:

- 1. `CC` 2022-05-31T21:00:00+00:00: KIS PnL -278.567104, cost 5.233163, action `reduce`.
- 2. `AVGO` 2022-03-31T21:00:00+00:00: KIS PnL -92.445057, cost 4.744956, action `exit`.
- 3. `CBT` 2022-02-28T21:00:00+00:00: KIS PnL -88.49845, cost 6.159543, action `hold`.
- 4. `AME` 2022-04-30T21:00:00+00:00: KIS PnL -71.609492, cost 4.49751, action `reduce`.
- 5. `ALSN` 2022-07-31T21:00:00+00:00: KIS PnL -69.29542, cost 3.357054, action `exit`.
- 6. `ADM` 2022-08-31T21:00:00+00:00: KIS PnL -58.66196, cost 3.152314, action `hold`.
- 7. `AVGO` 2022-07-31T21:00:00+00:00: KIS PnL -46.678844, cost 3.043667, action `hold`.
- 8. `CB` 2022-03-31T21:00:00+00:00: KIS PnL -39.17191, cost 5.590199, action `reduce`.
- 9. `BMRN` 2022-08-31T21:00:00+00:00: KIS PnL -31.387631, cost 2.816314, action `hold`.
- 10. `AFG` 2022-06-30T21:00:00+00:00: KIS PnL -26.073354, cost 3.392626, action `hold`.

Repair candidates for the next task:

- `cost_aware_drawdown_window_cap`: Apply only when portfolio drawdown is already near -25% and expected edge is low after KIS cost.
- `loss_cluster_preentry_audit`: Audit MDD-window losing symbols for common pre-entry L2/L3/L4 weakness before any rule change.
- `thin_margin_trade_skip_probe`: Dry-run-only probe: skip trades whose KIS-cost adjusted edge is too small during stressed drawdown windows.

No selector, sizing, or exit policy was changed in this task. Outcomes are audit-only.

## No-Background Decision-Maker Report

Conclusion first: KIS cost did not destroy the strategy, but it pushed the worst drawdown window just past the -30% gate.

The economic loss in the window mostly came from bad trades. But the reason the formal -30% gate failed was the extra KIS cost drag.

Next step: build a preregistered KIS-cost-aware drawdown guard. Do not retune the selector from this audit alone.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2511_2520_kis_mdd_decomposition/`.
- Validator: `python scripts/trader_brain_2511_2520_kis_mdd_decomposition_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
