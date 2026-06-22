# Task1121-1130 PIT + Non-SEC As-Of Repair Gate

## Decision Summary

- Verdict: `blocked_continue_source_repair`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Replay executed: 0.
- Selection promoted: 0.
- Key metrics:
  - PIT membership rows audited: 4,410.
  - PIT pass rows: 0.
  - SEC feature rows audited against PIT: 3,689.
  - SEC feature rows PIT-blocked: 3,689.
  - non-SEC normalized candidate rows: 11,823.
  - non-SEC dynamic-use rows: 0.
  - fresh entry candidate rows: 6.
  - stale reentry blocked rows: 129.
  - continuous exposure episodes: 6.
- What changed: Task1121-1130 created the repair gate surfaces for PIT membership, non-SEC as-of events, and fresh-entry versus continuous-exposure separation.
- Next action: continue PIT membership source acquisition and non-SEC timestamp normalization before policy preregistration.

## Quant Expert Report

### Data source and source readiness

- Inputs:
  - `data/artifacts/task_881_890_historical_brain_backtest_prep/universe_membership_panel.csv`
  - `data/artifacts/task_1081_1100_sec_asof_source_replay/task1082_sec_asof_adapter_feature_panel.csv`
  - `data/artifacts/task_1111_1120_pre_replay_audit_program/task1115_reentry_freshness_ledger.csv`
  - `data/artifacts/task_1111_1120_pre_replay_audit_program/task1116_continuous_thesis_exposure_ledger.csv`
  - `data/raw/macro_fred/task_655/fred_macro_release_repaired_feature_panel.csv`
  - `data/raw/task_636_content_source_text/task_636_source_text_checkpoint.csv`
- PIT source state:
  - Current universe remains reference-only.
  - 4,410 decision-symbol membership rows are audited but 0 pass PIT membership.
- non-SEC source state:
  - `macro_fred` and non-SEC Task636 content text were normalized as candidates.
  - No row is dynamic-use allowed because received timestamps, explicit complete source-time, tag requirements, or vintage/as-of certification remain incomplete.

### Exact join keys

- PIT membership validation:
  - `symbol`
  - `theme`
  - `decision_asof_ts`
- SEC feature PIT join:
  - `symbol`
  - `theme`
  - `decision_asof_ts`
- Reentry boundary:
  - `policy_variant_id`
  - `trade_spec_id`
  - `thesis_fingerprint`

### Leakage audit

- No replay was executed.
- No selection was promoted.
- Missing PIT membership is blocked, not treated as a negative label.
- non-SEC candidates remain feature-only and blocked from dynamic use.
- Forbidden outcome columns remain excluded from repair-gate assignment logic.

### Split/OOS metrics

- Not applicable.
- This task did not run a new backtest.

### Failure decomposition

- PIT universe:
  - 0/4,410 PIT membership rows pass.
  - 0/3,689 SEC feature rows pass PIT join.
- non-SEC dynamic source:
  - 11,823 candidate rows are normalized after excluding SEC company-submission rows from Task636.
  - 0 candidate rows are dynamic-use allowed.
- Trading judgment:
  - 6 selected rows are first-entry candidates.
  - 129 rows remain stale reentries.
  - 6 exposure episodes require structural-hold preregistration.

### Remaining blockers

- PIT membership evidence needs effective start/end, published, received, available-to-brain timestamps, raw path, and hash.
- non-SEC event evidence needs raw hash plus published, received, available-to-brain timestamps in the same row.
- Macro FRED candidate rows require vintage/as-of certification before dynamic use.
- Task636 content text excludes SEC company-submission rows and still requires source-time repair before dynamic use.

## No-Background Decision-Maker Report

What happened:

We built the next repair gate, but it did not unlock replay.

Why it matters:

The project now has a cleaner machine-readable boundary between source candidates and usable as-of trading evidence.

Whether this changes capital/deployment readiness:

No. Strategy remains `NOT_ACCEPTED`. Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`. Real capital remains `FORBIDDEN`.

Plain-language next step:

Keep repairing evidence. Do not run a new strategy backtest yet.

## Artifact Manifest

### Outputs

- `data/artifacts/task_1121_1130_pit_nonsec_repair/task1121_pit_membership_schema_contract.csv`
- `data/artifacts/task_1121_1130_pit_nonsec_repair/task1122_pit_source_catalog.csv`
- `data/artifacts/task_1121_1130_pit_nonsec_repair/task1123_pit_membership_validation_panel.csv`
- `data/artifacts/task_1121_1130_pit_nonsec_repair/task1124_trade_spec_pit_join_audit.csv`
- `data/artifacts/task_1121_1130_pit_nonsec_repair/task1125_nonsec_event_schema_contract.csv`
- `data/artifacts/task_1121_1130_pit_nonsec_repair/task1126_nonsec_normalized_event_candidates.csv`
- `data/artifacts/task_1121_1130_pit_nonsec_repair/task1127_nonsec_event_validation_panel.csv`
- `data/artifacts/task_1121_1130_pit_nonsec_repair/task1128_fresh_entry_candidate_ledger.csv`
- `data/artifacts/task_1121_1130_pit_nonsec_repair/task1128_continuous_exposure_episode_ledger.csv`
- `data/artifacts/task_1121_1130_pit_nonsec_repair/task1129_integrated_pre_replay_gate.csv`
- `data/artifacts/task_1121_1130_pit_nonsec_repair/task1130_pit_nonsec_repair_closeout.csv`
- `data/artifacts/task_1121_1130_pit_nonsec_repair/task1130_pit_nonsec_repair_closeout.json`
- `data/artifacts/task_1121_1130_pit_nonsec_repair/artifact_manifest.csv`

### Validation Commands

```text
python scripts/trader_brain_1121_1130_pit_nonsec_repair.py
python scripts/task_artifact_manifest.py --task-dir data/artifacts/task_1121_1130_pit_nonsec_repair
python scripts/trader_brain_1121_1130_pit_nonsec_repair_validate.py
python -m unittest tests.test_trader_brain_1121_1130_pit_nonsec_repair
python scripts/task_registry_validate.py --registry tasks/task_registry.csv --root .
```

Validation authority: `GOVERNANCE_HEALTH`; `DIAGNOSTIC_PRE_REPLAY_REPAIR_GATE_ONLY`.

PASS means the Task1121-1130 governance artifacts preserve PIT membership, source-time, and no-replay boundaries.
PASS does not mean strategy acceptance, deployment readiness, broker truth completion, PnL validity, source completeness, or real-capital permission.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
