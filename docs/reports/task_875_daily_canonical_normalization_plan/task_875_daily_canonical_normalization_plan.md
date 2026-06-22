# Task875 Daily Canonical Normalization Plan

## Decision Summary

- Verdict: executed for explicit harness symbols.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Purpose: normalize daily candidate data into canonical replay-safe bars.

## Quant Expert Report

Daily normalization must:

- add explicit symbol where missing through a certified manifest map;
- attach provider/source/hash;
- attach adjustment policy and corporate action source;
- output canonical columns only;
- keep legacy raw data unchanged.

## No-Background Decision-Maker Report

The existing daily data can be useful, but it needs a clean certified layer before replay.

Execution update:

- Canonical daily files were produced for all 16 explicit harness symbols.
- Coverage: 2021-01-04 through 2026-06-12.
- Canonical status: 16 ok.

## Artifact Manifest

- Output: `data/artifacts/task_870_879_full_controlled_replay/daily_canonical_manifest.csv`.
- Canonical files: `data/artifacts/task_870_879_full_controlled_replay/canonical_daily/`.
- Validation command: `python scripts/trader_brain_870_879_full_replay_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
