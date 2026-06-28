# L3 Economic Meaning Engine Hardening Report

## Decision Summary

Verdict: L3 v2 diagnostic scaffolding was added while legacy behavior remains
available.

Strategy acceptance status: `NOT_ACCEPTED`.

Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.

Real capital status: `FORBIDDEN`.

What changed:

- Added `src/brain/l3` contracts and deterministic component scoring.
- Added source reliability, event prior, freshness decay, source gap taxonomy,
  evidence edge, relation graph, and contradiction modules.
- Added Task742 legacy compatibility shims.
- Added focused L3 unit tests and validator scripts.
- Added L3 architecture SSOT and code complexity audit.

Next action: migrate real economic interpretation rules into `src/brain/l3`
only after dependency mapping of historical Task742 artifacts.

## Quant Expert Report

### Goal Intake

Objective: harden L3 as a diagnostic-only economic meaning and evidence graph
layer while preserving legacy Task742 behavior.

Target metrics:

- L3 v2 package exists under `src/brain/l3`.
- Static confidence and calibrated probability are separated.
- Noncritical not-ready evidence does not block the whole graph.
- Critical source blockers still block the graph.
- Validators prove no trade, score, or order intent outputs.

Forbidden actions:

- No inferred lifecycle matching.
- No symbol/date/price/time proximity fallback.
- No fake source.
- No unavailable raw source approximation.
- No label leakage.
- No BUY/SELL signal.
- No rank, sizing, or order intent.
- No broker mutation.
- No paper trading or live trading permission.

Available raw sources: no new raw sources were acquired. Existing local L2
contracts and runtime adapters are available.

Missing raw sources: no new source acquisition was attempted; calibrated
historical outcome tables are still missing.

Owner team: Research Governance.

Reviewer teams: Data & Market Microstructure, Backtest & Simulation Infra,
Execution & Risk.

Artifact locations:

- `docs/architecture/l3_economic_meaning_engine_architecture.md`
- `docs/reports/task_l3_economic_meaning_hardening/`
- `src/brain/l3/`

Validation commands are listed below.

Completion criteria: legacy compatibility preserved, new diagnostic contracts
and tests added, safety boundaries preserved.

Failure criteria: any L3 output emits trade/rank/order intent or static
confidence is labeled as empirical probability.

### Current L3 Implementation Diagnosis

The local workspace did not contain the GitHub-visible `src/brain/meaning_adapter.py`,
`src/brain/relation_adapter.py`, or `src/brain/contracts.py` files named in the
incoming task brief. It did contain `src/brain/l2_to_meaning_adapter.py` and a
canonical L2 primitive contract. This task therefore added compatibility shims
for the legacy Task742 path and added the new diagnostic v2 path in parallel.

Known historical facts from the incoming task brief are preserved as context:

- Task742 packets adapted to L3 EconomicMeaning: 3,443.
- Relation edges / thesis bundles: 228.
- `SUPPORTS_THESIS`: 0.
- `RISKS_THESIS`: 0.
- `MIXED_CONTEXT`: 33.
- `CONTEXT_ONLY`: 5.
- `BLOCKED_NOT_READY`: 190.
- Existing L3/L4 path is review-only.

### Code Complexity And Responsibility Audit

The detailed audit is in:

`docs/reports/task_l3_economic_meaning_hardening/l3_code_complexity_audit.md`

The key finding is that L3 complexity is primarily a responsibility placement
problem. Economic interpretation should be owned by `src/brain/l3` when used by
runtime brain contracts.

### Static Confidence Limitation

Static confidence is not empirical probability.

This task does not create historical hit-rate calibration. `medium -> 0.60`
remains a static diagnostic weight only.

### New Confidence Component Model

`L3Confidence` separates:

- `raw_band`
- `static_weight`
- `calibrated_probability`
- `calibration_status`
- `calibration_version`
- `sample_size`
- `brier_score`
- `calibration_error`

`calibrated_probability` is `None` unless the status is `CALIBRATED`.

### Source Reliability Model

Source reliability is config-backed:

`configs/brain/l3_source_reliability.yaml`

Initial classes include official primary, SEC primary, company IR primary,
licensed metadata proxy, news discovery proxy, uncertified source, and missing
source.

### Event Prior Model

Event priors are config-backed:

`configs/brain/l3_event_type_priors.yaml`

Initial priors are interpretation-strength priors, not investment success
probabilities.

### Freshness Decay Model

Freshness decay is deterministic:

```text
freshness_decay = 0.5 ** (age_minutes / half_life_minutes)
```

Config lives at:

`configs/brain/l3_freshness_decay.yaml`

### Evidence-Edge Graph Model

`L3EvidenceEdge` carries component scores and an edge state. `L3RelationGraph`
aggregates:

- `support_score`
- `risk_score`
- `context_score`
- `blocker_score`
- `net_direction_score`
- `coverage_score`

Graph states are review-only states.

### Critical Blocker Vs Noncritical Gap

The new source gap taxonomy separates critical blockers from noncritical gaps.
A noncritical `not_ready` confirmation gap does not block the whole graph. A
critical missing raw source still sets `BLOCKED_CRITICAL`.

### Legacy Compatibility Statement

`src/brain/meaning_adapter.py` and `src/brain/relation_adapter.py` are legacy
review-only shims. Legacy `not_ready` all-or-nothing blocking is preserved.

### Leakage Audit

No labels or outcomes are used by the new L3 v2 assignment logic. No inferred
matching was used. Missing labels were not treated as negatives. Missing raw
sources were reported as source gaps and were not approximated.

### Validation Commands And Results

Passed:

```text
python -m py_compile src\brain\meaning_adapter.py src\brain\relation_adapter.py src\brain\contracts.py src\brain\l3\contracts.py src\brain\l3\confidence.py src\brain\l3\source_reliability.py src\brain\l3\event_priors.py src\brain\l3\freshness_decay.py src\brain\l3\evidence_edge.py src\brain\l3\relation_graph.py src\brain\l3\graph_aggregator.py src\brain\l3\source_gaps.py src\brain\l3\contradiction.py src\brain\l3\adapters\task742_legacy_adapter.py src\brain\l3\adapters\l2_primitive_adapter.py
python -B -m unittest tests.test_l3_confidence_components tests.test_l3_source_reliability tests.test_l3_event_priors tests.test_l3_freshness_decay
python -B -m unittest tests.test_l3_evidence_edge_graph tests.test_l3_contradiction_detection tests.test_l3_legacy_compatibility
python -B -m unittest tests.test_l2_canonical_primitive_hardening tests.test_l2_live_runtime_canonical_path
python -B scripts/validate_l3_confidence_not_probability.py
python -B scripts/validate_l3_evidence_graph_contract.py
python -B scripts/validate_l3_no_trade_outputs.py
python -B scripts/validate_l3_legacy_compatibility.py
python -B scripts/validate_l3_source_gap_taxonomy.py
python -B scripts/task_registry_validate.py
python -B scripts/active_task_registry_validate.py
python -B scripts/governance_completion_audit.py
```

Execution notes:

```text
The first sandboxed py_compile attempt failed on __pycache__ rename permissions.
The first sandboxed L2 regression attempt failed on tempfile permissions.
Both passed when rerun with approved execution.
Governance audit passed with pre-existing protected DB DVC warnings only.
```

### Safety Boundaries Preserved

This task does not grant strategy acceptance.

This task does not grant deployment readiness.

This task does not grant paper trading.

This task does not grant live trading.

This task does not permit broker mutation.

This task does not create BUY/SELL signals.

This task does not create rank, sizing, or order intent.

L3 v2 outputs are diagnostic/review-only.

Static confidence is not empirical probability.

### Remaining Blockers

- Historical calibration outcome tables do not exist yet.
- Task742 historical rules were not migrated because the named backtest files
  are absent in this local snapshot.
- Full governance audit may still fail due unrelated pre-existing repository
  conditions or sandbox temp/pycache permissions.

### Next Recommended Tasks

1. Build event-family historical outcome tables for calibration audit.
2. Add OOS calibration reports with Brier score and reliability diagrams.
3. Dependency-map historical Task742 artifacts before migrating old rules.
4. Extend L2 primitive-to-L3 mapping for real event families and economic
   dimensions.

## No-Background Decision-Maker Report

L3 now has a safer diagnostic structure. It can explain source reliability,
confidence components, event priors, freshness decay, blockers, and evidence
graph state without pretending that a static weight is a probability.

This does not change capital readiness. It is still diagnostic-only and not
deployment-ready.

The practical next step is calibration data, not trading.

## Artifact Manifest

Inputs:

- Existing L2 primitive contract.
- Existing L2-to-meaning adapter.
- Incoming L3 hardening task specification.

Outputs:

- L3 architecture SSOT.
- L3 v2 code package.
- Legacy compatibility shims.
- L3 validators.
- L3 tests.
- This report and decision CSV.

Row counts:

- New raw data rows: 0.
- New L3 production outputs: 0.
- New tests: 7 files.
- New validators: 5 files.

File sizes and hashes are not source-critical for this diagnostic-only report.
