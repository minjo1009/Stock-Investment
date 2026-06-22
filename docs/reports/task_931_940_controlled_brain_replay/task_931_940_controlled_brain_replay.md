# Task931-940 Controlled Brain Replay

## Decision Summary

- Verdict: first controlled brain replay executed as diagnostic only.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Period: 2021-01-01 through 2026-03-31.
- Initial capital: 1,000 USD.
- Benchmark: QQQ same-window buy-and-hold.
- Input trade specs: 3,689.
- Closed trades: 3,507.
- Skipped orders: 182.
- Open positions at end: 0.
- Strategy final equity: 1,822.12.
- Strategy total return: 82.212006%.
- Strategy CAGR: 12.144534%.
- Strategy max drawdown: -39.490255%.
- QQQ final equity: 1,925.31.
- QQQ total return: 92.531231%.
- QQQ CAGR: 13.330905%.
- Decision: strategy made money but underperformed QQQ and failed the recent OOS-2 window.
- Next action: run failure decomposition before changing adapter policy.

## Quant Expert Report

The replay used this chain:

```text
Task929 controlled trade specs
-> exact daily adjusted close entry and exit prices
-> long-only fractional-share cash-limited execution
-> cost and slippage adjustment
-> split, theme, equity, and governance summaries
```

Execution model:

- Entry: exact `tradable_after_ts` session adjusted close.
- Exit: exact `planned_exit_not_after_ts` session adjusted close.
- No nearest-date fallback.
- Long-only.
- Fractional shares allowed.
- Same entry-date orders are scaled pro rata to available cash.
- Entry slippage: 5 bps.
- Exit slippage: 5 bps.
- Additional round-trip cost: 10 bps.

Split result:

```text
development_2021_2024: +717.346576 PnL, 1.976773% return on spent
oos_1_2025: +202.138036 PnL, 1.769692% return on spent
oos_2_2026_q1: -97.364414 PnL, -3.408247% return on spent
```

Theme result:

```text
power_grid_electrification: +3.298718% return on spent
ai_semiconductors: +3.566315% return on spent
crypto_fintech: +2.621506% return on spent
data_devops_software: -0.453697% return on spent
```

The strategy did not beat QQQ over the same window:

```text
Strategy: 1000 -> 1822.12
QQQ:      1000 -> 1925.31
```

Failure decomposition:

- The full-period return is positive but benchmark-relative weak.
- Recent OOS-2 is negative.
- Max drawdown is high at -39.490255%.
- 182 orders were skipped because cash was unavailable after pro-rata scaling.
- The current adapter policy is too broad and mostly behaves like a recurring long-only thematic exposure layer.

## No-Background Decision-Maker Report

We finally ran the controlled brain replay.

It did not collapse. It turned 1,000 dollars into 1,822.12 dollars.

But QQQ turned 1,000 dollars into 1,925.31 dollars over the same window. So this is not good enough. The recent 2026Q1 OOS slice also lost money. The next task should not be more data collection or a bigger run. It should diagnose why the brain-generated candidate set becomes too broad and why it fails to beat QQQ after costs.

## Artifact Manifest

- Script: `scripts/trader_brain_931_940_controlled_replay.py`.
- Validator: `scripts/trader_brain_931_940_controlled_replay_validate.py`.
- Test: `tests/test_trader_brain_931_940_controlled_replay.py`.
- Trades: `data/artifacts/task_931_940_controlled_brain_replay/task931_controlled_replay_trades.csv`.
- Equity curve: `data/artifacts/task_931_940_controlled_brain_replay/task932_controlled_replay_equity_curve.csv`.
- Split summary: `data/artifacts/task_931_940_controlled_brain_replay/task933_controlled_replay_by_split.csv`.
- Theme summary: `data/artifacts/task_931_940_controlled_brain_replay/task934_controlled_replay_by_theme.csv`.
- Skipped orders: `data/artifacts/task_931_940_controlled_brain_replay/task935_controlled_replay_skipped_orders.csv`.
- Summary: `data/artifacts/task_931_940_controlled_brain_replay/task936_controlled_replay_summary.json`.
- Source manifest: `data/artifacts/task_931_940_controlled_brain_replay/task937_replay_source_manifest.csv`.
- Governance closeout: `data/artifacts/task_931_940_controlled_brain_replay/task940_governance_closeout.csv`.
- Validation command: `python scripts/trader_brain_931_940_controlled_replay_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
