# Task1111-1120 Pre-Replay Audit Program

## Decision Summary

- Verdict: `pre_replay_audit_blocks_next_replay_until_pit_and_dynamic_sources_are_repaired`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Audited variant: `sec_slot3_theme_cap1_v1`.
- Key metrics:
  - PIT universe rows: 70.
  - PIT membership verified rows: 0.
  - Trade specs audited: 3,689.
  - Trade specs blocked by PIT: 3,689.
  - Selected reentry rows: 135.
  - Stale same-score reentries: 129.
  - Continuous exposure chains: 6.
  - Non-SEC source families inventoried: 7.
  - Non-SEC families dynamic-use allowed: 0.
  - Replay executed: 0.
- What changed: the next replay gate now has explicit PIT universe, stale reentry, structural-hold preregistration, and non-SEC dynamic-source audit artifacts.
- Next action: repair PIT universe source dates and build a normalized non-SEC as-of event panel before any new replay.

## Quant Expert Report

### Data source and source readiness

- Inputs:
  - `data/raw/theme_universe_10x7.csv`
  - `data/artifacts/task_1081_1100_sec_asof_source_replay/task1082_sec_asof_adapter_feature_panel.csv`
  - `data/artifacts/task_1081_1100_sec_asof_source_replay/task1083_sec_asof_selection_ledger.csv`
  - `data/artifacts/task_1081_1100_sec_asof_source_replay/task1084_sec_asof_replay_trades.csv`
- `theme_universe_10x7.csv` remains a fixed research universe, not a point-in-time tradable universe.
- SEC companyfacts source-time still passes inside its own scope, but it does not prove point-in-time universe membership.
- Non-SEC raw families exist, including macro, policy, factor, research, and event-text candidates, but they are not yet normalized into one row with raw hash plus published, received, and available-to-brain timestamps.

### Exact join keys

- PIT universe audit:
  - `symbol`
  - `theme`
  - `decision_asof_ts`
- Reentry audit:
  - `policy_variant_id`
  - `symbol`
  - `trade_spec_id`
  - `thesis_fingerprint`
- Dynamic source shadow audit:
  - `policy_variant_id`
  - `trade_spec_id`
  - `decision_asof_ts`
  - `symbol`
  - `theme`

### Leakage audit

- No replay was executed.
- No PnL, future return, outcome rank, or post-entry price field enters any assignment rule.
- Missing PIT membership is blocked, not treated as a negative label.
- Static universe rows are blocked from selection and replay use.
- Non-SEC source families with timestamp candidates remain blocked until exact source-time normalization is complete.

### Split/OOS metrics

- Not applicable.
- This task is a pre-replay gate and did not run a new backtest.

### Failure decomposition

- PIT universe:
  - 70/70 universe rows lack PIT membership timestamps.
  - 3,689/3,689 adapter feature rows are blocked by missing PIT membership.
- Reentry:
  - `sec_slot3_theme_cap1_v1` has 135 selected rows.
  - 129 selected rows are stale same-score reentries.
  - 6 continuous exposure chains explain the selected set.
- Non-SEC dynamic source:
  - 7 source families were inventoried.
  - 0 source families are approved for dynamic selection or replay use.
  - Macro FRED has timestamp-like candidates, but vintage/as-of certification and single-row raw-hash/time normalization remain incomplete.

### Cost/slippage stress

- Not applicable.
- No replay or trade generation was executed.

### Remaining blockers

- PIT universe membership evidence with raw source path, source hash, effective start/end, published, received, and available-to-brain timestamps.
- Normalized non-SEC as-of event panel joining raw hash, source time, event category, symbol/theme tags, and confidence fields.
- A future replay policy must be preregistered after these two blockers pass.

## No-Background Decision-Maker Report

What happened:

We built the gate that stops the suspicious high-return SEC-only result from being treated as real strategy skill.

Why it matters:

The high result is still mostly a narrow winner basket. The project now explicitly separates “new trade judgment” from “same thesis exposure repeated many times.”

Whether this changes capital/deployment readiness:

No. Strategy remains `NOT_ACCEPTED`. Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`. Real capital remains `FORBIDDEN`.

Plain-language next step:

Do not run another celebratory backtest yet. First repair PIT universe evidence and make non-SEC event timing usable as-of.

## Artifact Manifest

### Outputs

- `data/artifacts/task_1111_1120_pre_replay_audit_program/task1111_pit_universe_source_catalog.csv`
- `data/artifacts/task_1111_1120_pre_replay_audit_program/task1112_pit_membership_panel.csv`
- `data/artifacts/task_1111_1120_pre_replay_audit_program/task1113_trade_spec_pit_join_audit.csv`
- `data/artifacts/task_1111_1120_pre_replay_audit_program/task1114_pit_block_ledger.csv`
- `data/artifacts/task_1111_1120_pre_replay_audit_program/task1115_reentry_freshness_ledger.csv`
- `data/artifacts/task_1111_1120_pre_replay_audit_program/task1116_continuous_thesis_exposure_ledger.csv`
- `data/artifacts/task_1111_1120_pre_replay_audit_program/task1117_structural_hold_policy_preregistration.csv`
- `data/artifacts/task_1111_1120_pre_replay_audit_program/task1118_non_sec_source_time_panel.csv`
- `data/artifacts/task_1111_1120_pre_replay_audit_program/task1119_dynamic_event_shadow_ranking.csv`
- `data/artifacts/task_1111_1120_pre_replay_audit_program/task1120_external_audit_closeout.csv`
- `data/artifacts/task_1111_1120_pre_replay_audit_program/task1120_external_audit_closeout.json`
- `data/artifacts/task_1111_1120_pre_replay_audit_program/artifact_manifest.csv`

### Validation Commands

```text
python scripts/trader_brain_1111_1120_pre_replay_audit_program.py
python scripts/task_artifact_manifest.py --task-dir data/artifacts/task_1111_1120_pre_replay_audit_program
python scripts/trader_brain_1111_1120_pre_replay_audit_program_validate.py
python -m unittest tests.test_trader_brain_1111_1120_pre_replay_audit_program
python scripts/task_registry_validate.py --registry tasks/task_registry.csv --root .
```

Validation authority: `DIAGNOSTIC_PRE_REPLAY_AUDIT_ONLY`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
