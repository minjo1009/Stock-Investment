# Task 076 Review

- source report: `docs\reports\task_076\task_076_minimal_regime_entry_gate.json`
- baseline candidate: `A_BASELINE`
- selected candidate: `H_KER_VOLUME_DAILY_BIAS`

## S4 Snapshot

- baseline PF/Net/MDD/Sharpe/Trades: 1.1684 / 8373.70 / 8919.73 / 0.7238 / 186
- candidate PF/Net/MDD/Sharpe/Trades: 1.9232 / 10922.50 / 2183.55 / 1.5448 / 45

## Checks
- trade_count_ok: False
- pf_improved: True
- sharpe_improved: True
- mdd_improved: True
- net_reasonable: True

## Decision
- gate decision: FAIL
- pilot answer: NO
- recommendation: DISCARD_AND_KEEP_BASELINE
