# Task876 Intraday 15m Canonical Normalization Plan

## Decision Summary

- Verdict: executed for explicit harness symbols.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Purpose: normalize mixed 15m schemas and regular-hours policy.

## Quant Expert Report

Task855 found two schemas:

- `timestamp, open, high, low, close, volume`
- `timestamp, open, high, low, close, volume, trade_count, vwap`

Task876 must create a canonical 15m output without silently fabricating `trade_count` or `vwap`.

## No-Background Decision-Maker Report

The 15m data is large, but it cannot be used until its schema and market-hours policy are clean.

Execution update:

- Canonical 15m files were produced for all 16 explicit harness symbols.
- New recent 15m downloads cover 2026-03-19 through 2026-06-12.
- Existing task data was preserved and merged where available.
- Canonical status: 16 ok.

## Artifact Manifest

- Output: `data/artifacts/task_870_879_full_controlled_replay/intraday_15m_canonical_manifest.csv`.
- Canonical files: `data/artifacts/task_870_879_full_controlled_replay/canonical_intraday_15m/`.
- Validation command: `python scripts/trader_brain_870_879_full_replay_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
