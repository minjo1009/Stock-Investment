# Task 545 Factor-Adjusted Failure-State Suppression

## Decision Summary

- Strategy acceptance: FACTOR_ADJUSTED_SUPPRESSION_DIAGNOSTIC_NO_FIRM_PASS
- Suppression rules tested: 6
- Walk-forward pass count: 0
- Best overall rule: remove_breakout_high_close_low_vwap
- Deployment-ready: NO

## Quant Expert Report

Task545 tests entry-safe suppression variants for the failure states identified in Task544.
Rules are assigned without using exit reason, residual outcome, or labels; those fields are evaluation-only.
remove_breakout_high_close_low_vwap: count 3560, residual -0.27%, entry_reduce 33.15%.
remove_opening_drive_weak_acceptance: count 3545, residual -0.29%, entry_reduce 33.26%.
remove_volume_reclaim_weak_theme: count 3575, residual -0.34%, entry_reduce 33.09%.

## No-Background Decision-Maker Report

We tried to remove the recurring bad continuation patterns without using future information.
The goal is to keep enough trades while reducing entry-reduce failures and preserving factor-adjusted residual returns.
This remains diagnostic until it survives walk-forward and live-source constraints.

## Artifact Manifest

See `artifact_manifest.csv`.
