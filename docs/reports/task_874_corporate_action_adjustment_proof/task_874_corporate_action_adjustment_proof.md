# Task874 Corporate Action Adjustment Proof

## Decision Summary

- Verdict: executed for explicit harness symbols.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Purpose: attach split/dividend/adjustment proof for replay symbols.

## Quant Expert Report

Required fields:

```text
symbol
action_date
action_type
split_factor
dividend_amount
adjustment_factor
provider
source_file_sha256
data_available_ts
```

Without this, daily adjusted replay and daily/15m consistency cannot pass.

## No-Background Decision-Maker Report

Price history must be adjusted consistently before comparison to QQQ or any strategy result.

Execution update:

- Corporate action files were acquired for all 16 explicit harness symbols.
- Adjustment proof is recorded in the task-scoped corporate action manifest.
- Replay uses adjusted close for entry and exit.

## Artifact Manifest

- Output: `data/artifacts/task_870_879_full_controlled_replay/corporate_action_adjustment_manifest.csv`.
- Validation command: `python scripts/trader_brain_870_879_full_replay_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
