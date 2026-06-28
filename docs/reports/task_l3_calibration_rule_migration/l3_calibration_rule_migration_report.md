# L3 Calibration Outcome Contract and Task742 Rule Migration Report

## Decision Summary

- Verdict: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- What changed: L3 now has a governed calibration outcome table contract,
  guarded builder, SQLite store, calibration audit buckets, and a recovered
  Task742 rule migration module.
- Key result: calibration rows cannot be built through inferred matching.
- Key result: an exact canonical source-event to lifecycle/outcome bridge was
  built with 4,073 diagnostic bridge rows.
- Key result: that bridge produced 4,073 L3 diagnostic calibration outcome rows,
  2,686 non-missing labels, 20 audit buckets, and 10 calibrated diagnostic
  buckets.
- Key result: Task742 recovered rules produce L3 diagnostic meanings with no
  trade, score, sizing, rank, or order-intent output.
- Key result: renamed/local artifact schema search found no Task742 packet
  candidate with `source_circuit` and Task742 output columns.
- Next action: build a Task742 packet to outcome bridge artifact before any
  Task742-specific empirical calibration probability is used.

## Quant Expert Report

### Goal Intake

Objective: progress L3 calibration and Task742 rule migration under the project
operating cycle without opening any trading boundary.

Target metrics:

- Calibration outcome contract exists.
- Calibration builder rejects inferred matching.
- Calibration audit bucket computes Brier score and calibration error only when
  sample size is sufficient.
- Task742 recovered event-family rules exist under `src/brain/l3`.
- Tests and validators cover calibration safety and rule migration safety.

Forbidden actions:

- No symbol/date/price/time fallback matching.
- No inferred lifecycle matching.
- No fake source.
- No unavailable raw source approximation.
- No label leakage.
- No unlabeled row to negative conversion.
- No BUY/SELL, rank, sizing, or order intent.
- No broker mutation.
- No strategy acceptance or deployment claim.

Available data:

- Local L2 primitive contracts and L3 v2 contracts.
- Local L2 news smoke artifact described by TaskL2NewsCanonicalPath.
- Local OOS reports with lifecycle-level outcomes, but without L3 meaning ids.
- Canonical source-event artifacts with explicit `source_event_id` and
  `lifecycle_id` keys.
- GitHub-recovered Task742 source files for rule migration provenance.

Missing data:

- Task742 packet artifacts with row-level keys that can be joined to lifecycle
  outcomes without inference.
- A full golden-output comparison against the 3,443 historical Task742 packets.

Owner team: Research Governance.

Reviewer teams: Backtest & Simulation Infra, Data & Market Microstructure,
Execution & Risk.

Output directory:

```text
docs/reports/task_l3_calibration_rule_migration/
```

Large artifact directory: not used.

Validation: unit tests, validator scripts, registry validation, governance
audit.

### Subagent Usage

Two read-only explorer subagents were used with bounded packets:

- Calibration data explorer: audited available L2/L3 inputs, OOS outcome panels,
  join keys, missing bridge keys, and leakage risks.
- Task742 recovery explorer: audited local Task742 rule availability and safe
  migration boundaries.

Both explorers had no write scope.

### Calibration Contract

New files:

```text
src/brain/l3/calibration_bridge.py
src/brain/l3/calibration_bridge_search.py
src/brain/l3/calibration_contracts.py
src/brain/l3/calibration_builder.py
src/brain/l3/calibration_store.py
src/brain/l3/calibration_apply.py
docs/contracts/l3_calibration_outcome_contract.md
```

The builder accepts only explicit bridge keys matching the meaning id, L2
primitive id, or source receipt id. It rejects inferred matching.

`L3OutcomeBridgeRow` now defines the bridge artifact that must exist before
historical OOS lifecycle panels can be used for row-level L3 calibration.

`calibration_bridge_builder.py` and
`scripts/build_l3_calibration_bridge_eligibility_audit.py` automate the current
bridge eligibility scan and regenerate `l3_calibration_bridge_gap_audit.csv`.

`calibration_bridge_search.py` and
`scripts/build_l3_explicit_bridge_search_audit.py` search exact
`source_event_id -> lifecycle_id -> outcome` paths. This produced
`l3_explicit_source_event_outcome_bridge.csv` with 4,073 rows.

SQLite tables:

```text
l3_calibration_outcomes
l3_calibration_audit_buckets
```

### Calibration Result And Limitation

Current local evidence is enough to produce a canonical source-event diagnostic
calibration seed, but not enough to produce Task742-specific calibrated
probabilities.

Generated diagnostic calibration artifacts:

```text
l3_explicit_source_event_outcome_bridge.csv rows = 4,073
l3_calibration_outcomes.csv rows = 4,073
non_missing_outcome_rows = 2,686
l3_calibration_audit_buckets.csv rows = 20
calibrated_diagnostic_buckets = 10
```

These calibrated diagnostic buckets are for canonical source-event bridge
states with `direction = UNKNOWN`. They are not BUY/SELL signals and they are
not Task742 economic-rule calibrated probabilities.

The bridge eligibility audit currently reports:

```text
candidate_count = 3
allowed_for_calibration = 0
rejection_reason = missing_l3_bridge_key
```

That audit checks single-file L3 bridge eligibility. The newer exact bridge
search checks two-step explicit keys and found 9 buildable
`source_event_id -> lifecycle_id -> outcome` pairs. It still did not find a
Task742 packet to outcome bridge.

The Task742 packet bridge gap audit reports:

```text
task742_packet_bridge_candidates = 0
task742_packet_bridge_allowed = 0
sentinel = NO_LOCAL_TASK742_PACKET_ARTIFACT_FOUND
```

Because this project was reorganized, an additional schema-based search was
added so the audit does not depend on old file names. It scans local CSV, TSV,
JSONL, JSON, and SQLite schemas across the project, excluding only heavy source
dumps and generated/cache surfaces such as `data/raw`, `.git`, `.dvc`,
`frontend`, and `graphify-out`, for Task742 contract columns such as
`source_circuit`, `interpretation_state`, `economic_direction_hint`,
`confidence_band`, and `relation_ready_tier`. It also checks whether any packet
candidate has exact `source_event_id` overlap with the canonical bridge.

Current renamed-schema search result:

```text
task742_schema_search_candidates = 0
task742_schema_search_packet_candidates = 0
task742_schema_search_calibration_allowed = 0
canonical_bridge_unique_source_receipts = 1365
sentinel = NO_TASK742_SCHEMA_MATCH_FOUND
```

Remote GitHub report manifests reference the Task740/741/742 packet artifacts,
but the raw artifact URLs are not downloadable from the repository:

```text
remote_task742_artifacts_checked = 5
remote_task742_artifacts_downloadable = 0
http_status = 404
```

### Task742 Rule Migration

New files:

```text
src/brain/l3/task742_rules.py
src/brain/l3/adapters/task742_rule_adapter.py
docs/architecture/l3_task742_rule_migration_policy.md
```

Recovered rule families:

- Form 4 insider behavior.
- Ownership and activist control context.
- Credit/financing context.
- Financial results and guidance.
- Generic 8-K classifier context.

The adapter emits historical diagnostic L3 meanings:

```text
runtime_context = HISTORICAL_RESEARCH
source_time_certified = false
authority_class = uncertified_source
```

### Data Integrity Gate

Exact joins used in new unit tests:

- `outcome_bridge_key == meaning_id`
- `L3OutcomeBridgeRow.outcome_bridge_key == lifecycle_id`
- `source_event_id -> lifecycle_id -> outcome` exact-key bridge

Exact joins missing for real historical calibration:

- Task742 packet `source_event_id` to lifecycle/outcome rows.
- Full 3,443 packet Task742 golden-output replay to migrated L3 rules.

Inferred matching used: no.

Missing labels treated as negatives: no.

Missing raw sources approximated: no.

Labels/outcomes used in assignment logic: no.

### Validation Results

Passed:

```text
python -B -m unittest tests.test_l3_calibration_contracts tests.test_l3_task742_rule_migration
python -B scripts/validate_l3_calibration_contract.py
python -B scripts/validate_l3_task742_rule_migration.py
python -B -m unittest tests.test_l3_calibration_bridge
python -B scripts/validate_l3_calibration_bridge_contract.py
python -B -m unittest tests.test_l3_calibration_bridge_builder
python -B scripts/build_l3_calibration_bridge_eligibility_audit.py
python -B scripts/validate_l3_bridge_eligibility_audit.py
python -B scripts/build_l3_explicit_bridge_search_audit.py
python -B scripts/validate_l3_explicit_bridge_search_audit.py
python -B scripts/build_l3_calibration_outcome_table.py
python -B scripts/validate_l3_calibration_outcome_table.py
python -B scripts/build_l3_task742_packet_bridge_gap_audit.py
python -B scripts/validate_l3_task742_packet_bridge_gap_audit.py
python -B scripts/build_l3_task742_remote_artifact_availability_audit.py
python -B scripts/build_l3_task742_schema_search_audit.py
python -B scripts/validate_l3_task742_schema_search_audit.py
python -B -m unittest tests.test_l3_calibration_bridge_search
python -B -m unittest tests.test_l3_calibration_contracts tests.test_l3_task742_rule_migration tests.test_l3_confidence_components tests.test_l3_source_reliability tests.test_l3_event_priors tests.test_l3_freshness_decay tests.test_l3_evidence_edge_graph tests.test_l3_contradiction_detection tests.test_l3_legacy_compatibility
python -B scripts/validate_l3_no_trade_outputs.py
python -B scripts/validate_l3_legacy_compatibility.py
python -B scripts/validate_l3_source_gap_taxonomy.py
python -B -m unittest tests.test_l2_canonical_primitive_hardening tests.test_l2_live_runtime_canonical_path tests.test_l2_news_canonical_path
python -m py_compile src\brain\l3\calibration_contracts.py src\brain\l3\calibration_builder.py src\brain\l3\calibration_store.py src\brain\l3\calibration_apply.py src\brain\l3\task742_rules.py src\brain\l3\adapters\task742_rule_adapter.py scripts\validate_l3_calibration_contract.py scripts\validate_l3_task742_rule_migration.py tests\test_l3_calibration_contracts.py tests\test_l3_task742_rule_migration.py
python -B scripts/task_registry_validate.py
python -B scripts/active_task_registry_validate.py
python -B scripts/governance_completion_audit.py
```

Governance audit passed with pre-existing protected DB DVC warnings for
`trading.db` and `data/task388_intraday_canonical_continuation_engine.db`.

### Remaining Blockers

- Task742-specific empirical calibration requires a future Task742 packet to
  lifecycle/outcome bridge artifact.
- GitHub-visible Task740/741/742 reports contain manifests for the packet
  artifacts, but those large CSV/JSONL files are not present at raw URLs.
- Local renamed-schema search also found no CSV, JSONL, JSON, or SQLite table
  matching the Task742 packet schema across the project outside heavy raw/cache
  surfaces.
- The migrated Task742 rules are covered by representative unit tests, not a
  full golden-output comparison against 3,443 historical Task742 packets because
  those packet artifacts are not present locally.

### Safety Boundaries Preserved

This task does not grant strategy acceptance.

This task does not grant deployment readiness.

This task does not grant paper trading.

This task does not grant live trading.

This task does not permit broker mutation.

This task does not create BUY/SELL signals.

This task does not create rank, sizing, or order intent.

L3 calibration and Task742 migrated outputs are diagnostic/review-only.

Static confidence is not empirical probability.

## No-Background Decision-Maker Report

L3 now has the machinery needed to calibrate confidence correctly. It also has a
first exact canonical source-event bridge and a diagnostic outcome table.
However, this is not yet Task742-specific calibration. If there is no exact
bridge from an L3 meaning to a later outcome row, the calibration builder
refuses the row.

The Task742 rule logic has been recovered into the L3 package as historical,
diagnostic-only interpretation rules. That gives us rule migration progress
without turning old research rows into live trading evidence.

Capital and deployment status remain closed.

## Artifact Manifest

Inputs:

- L3 v2 contracts.
- L2 primitive contracts.
- GitHub-recovered Task742 source files listed in `source_provenance.csv`.
- Read-only subagent audits.

Outputs:

- Calibration outcome contract.
- Calibration builder/store/apply modules.
- Exact source-event bridge search module.
- Exact source-event to outcome bridge artifact.
- Diagnostic calibration outcome and audit bucket CSVs.
- Task742 recovered rule module and adapter.
- Tests and validators.
- Report, decision CSV, and source provenance.
