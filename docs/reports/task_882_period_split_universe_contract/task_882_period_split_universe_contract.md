# Task882 Period Split Universe Contract

## Decision Summary

- Verdict: planned.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Period: 2021-01-01 through 2026-03-31.
- Development split: 2021-01-01 through 2024-12-31.
- OOS-1 split: 2025-01-01 through 2025-12-31.
- OOS-2 split: 2026-01-01 through 2026-03-31.
- Universe: `data/raw/theme_universe_10x7.csv`.
- Benchmark: QQQ.
- Initial capital: `$1,000`.

## Quant Expert Report

This task freezes the scope before the brain or backtest code can move. The universe is explicit and not point-in-time top500. QQQ is benchmark-only. Split boundaries must be enforced by all downstream artifacts.

The universe is a fixed research universe for diagnostic historical replay. It must not be described as a point-in-time tradable universe unless future tasks attach symbol/theme inclusion evidence as-of each historical date.

## No-Background Decision-Maker Report

This prevents another wrong-size replay. The target is 10 themes x 7 symbols, not 16 symbols and not all available stocks.

## Artifact Manifest

- Planned output: `period_split_universe_contract.csv`.
- Validation command: `python scripts/trader_brain_881_890_historical_brain_backtest_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
