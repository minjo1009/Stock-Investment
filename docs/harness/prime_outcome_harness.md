# Prime Outcome Harness

## Purpose

Prime Outcome Harness makes every Codex task close with an explicit
`task_result_contract`.

The contract separates two things:

1. Actual underlying progress.
2. Valid diagnostic, design, review, or harness work that must not claim
   underlying progress.

This avoids a repeated loop where Codex writes reports, validators pass, and the
same problem remains unchanged.

## Core Abstraction

`task_result_contract` is the top-level unit.

`outcome_unit` is the thing expected to move.

`evidence_artifacts` prove that the movement, diagnosis, design, review, or
harness enforcement actually happened.

## Task Types

| task_type | Meaning | Underlying Progress Claim |
|---|---|---|
| `OUTCOME_CHANGE` | Moves a measured outcome unit | Allowed |
| `TERMINALIZE` | Converts pending/stale/retryable work into terminal status | Allowed within terminal scope |
| `RECLASSIFY` | Moves unknown/unmapped/unsupported rows into a justified class | Allowed within reclassification scope |
| `DIAGNOSTIC_ONLY` | Explains cause, scope, reproduction, or impact | Forbidden |
| `HARNESS_BOOTSTRAP` | Adds schema, validator, fixture, or guard capability | Forbidden for underlying domain progress |
| `EXPLORATORY_RESEARCH` | Gathers claims, sources, and open gaps | Forbidden |
| `DESIGN_ONLY` | Defines contract, ADR, interface, or plan | Forbidden |
| `REVIEW_ONLY` | Reviews work and selects next bounded target | Forbidden |

## Closeout Verdicts

| verdict | Meaning |
|---|---|
| `ACTUAL_PROGRESS` | Outcome unit moved with evidence |
| `ACTUAL_PROGRESS_WITH_RESIDUAL_BLOCKERS` | Outcome moved but residual blockers remain |
| `VALID_TERMINALIZATION` | Work was terminalized with reason and evidence |
| `VALID_RECLASSIFICATION` | Work was reclassified with traceable reason |
| `VALID_DIAGNOSTIC_ONLY` | Diagnostic work is valid, with no underlying progress claim |
| `VALID_DESIGN_ONLY` | Design work is valid, with no underlying progress claim |
| `VALID_REVIEW_ONLY` | Review work is valid, with no underlying progress claim |
| `VALID_HARNESS_BOOTSTRAP` | Harness enforcement was added, with no underlying progress claim |
| `BLOCKED_BY_UPSTREAM` | Task cannot progress because an upstream input is blocked |
| `INVALID_CLOSEOUT` | Contract, evidence, scope, safety, or claim is invalid |

## Global Rules

- Reports are not progress.
- Validator PASS alone is not progress.
- For tasks at or after `TASK-4172`, `task_result_contract.yaml` is mandatory.
- `validate_codex_closeout.py` must run the Prime contract validator before closeout.
- `scripts/ops/create_task.py` scaffolds a starter contract for every new task.
- Actual progress needs baseline, after measurement, same measurement method,
  evidence, and a compatible verdict.
- Diagnostic/design/review/harness work can be valid work, but must not claim
  underlying domain progress.
- Missing, stale, or incomplete data is `UNKNOWN/BLOCKER`, never negative
  evidence.
- Trading safety boundaries always remain closed.

## Layer Outcome Units

L0-L4 tasks should use one of the explicit layer outcome units below when they
claim actual underlying progress.

| layer | allowed outcome_unit examples |
|---|---|
| L0 | `failed_shard_count`, `incomplete_backfill_units`, `stale_realtime_collector_count`, `raw_integrity_error_count`, `collector_config_gap_count` |
| L1 | `unmapped_entity_count`, `unclassified_article_count`, `l1_blocked_packet_count`, `stale_l1_packet_count`, `missing_l1_materialization_count` |
| L2 | `blocked_feature_count`, `missing_materialization_count`, `unsupported_feature_source_count`, `feature_schema_gap_count`, `l1_l2_compatibility_gap_count` |
| L3 | `unsupported_relation_count`, `low_confidence_relation_count`, `missing_relation_evidence_count`, `relation_graph_quality_gap_count`, `orphan_relation_node_count` |
| L4 | `diagnostic_draft_blocker_count`, `missing_thesis_evidence_count`, `mixed_context_unresolved_count`, `institutional_quality_gap_count`, `thesis_bundle_blocker_count` |

## Safety Boundaries

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Broker mutation: `FORBIDDEN`
- Live order: `FORBIDDEN`
- Paper promotion: `FORBIDDEN`
