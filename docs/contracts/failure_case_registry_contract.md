# Failure Case Registry Contract

## Purpose

The Failure Case Registry is a diagnostic-only research contract for storing
success and failure cases in a common review format.

It supports future matched-pair analysis, failure similarity review, and
failure-learning reports. It does not tune assignment logic, rank candidates,
size positions, create order intent, promote paper trading, permit live orders,
or change strategy acceptance.

## Standing State

- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN

## Layer

- Input layer: L4 thesis and L5 diagnostic policy evidence.
- Output layer: research-only failure case rows.
- Runtime boundary: no L6 runtime mutation, no broker mutation, no paper/live
  order permission.

## Required Fields

| Field | Purpose |
| --- | --- |
| `trade_id` | Stable review id for the historical case. |
| `model_version` | Frozen model or policy version under review. |
| `feature_packet_hash` | Hash of the feature packet available at assignment time. |
| `source_lineage_status` | `strict`, `derived`, `proxy`, or `missing`. |
| `payoff_score` | Diagnostic score captured before outcome evaluation. |
| `winner_acceleration_score` | Diagnostic acceleration score captured before outcome evaluation. |
| `thesis_state` | Thesis state at decision time. |
| `entry_context` | Point-in-time context available before entry decision review. |
| `path_return_d1_d5_d20_d63` | Evaluation-only forward path returns. |
| `MAE` | Evaluation-only maximum adverse excursion. |
| `MFE` | Evaluation-only maximum favorable excursion. |
| `exit_reason` | Evaluation-only exit reason or review label. |
| `failure_type` | Evaluation-only failure category. |

## Hard Gates

- Future returns and outcome labels are evaluation-only.
- Outcome fields must not be used for assignment, calibration, candidate
  selection, candidate ranking, sizing, or policy routing.
- Missing labels are never negatives.
- Missing raw sources remain source gaps.
- No symbol/date/price/time proximity fallback may create a matched pair.
- Matching requires explicit case ids, feature packet hashes, model version, and
  point-in-time source lineage.
- The registry must not create `PolicyAction`, `RuntimeDecision`, paper order
  intent, live order permission, broker mutation, or replay execution.

## Allowed Use

- Store historical success and failure rows for review.
- Compare cases after assignment has already happened.
- Produce failure similarity evidence for human review.
- Explain why a diagnostic thesis or policy family failed.

## Forbidden Use

- Training or tuning assignment thresholds from future returns.
- Treating missing registry rows as bearish evidence.
- Creating buy, sell, reduce, exit, re-risk, size, allocation, order, paper, or
  live permission.
- Claiming strategy acceptance, deployment readiness, broker truth completion,
  or real-capital permission.

## Validation Authority

- `GOVERNANCE_HEALTH` for the contract and registry/report closeout.
- `PACKAGE_HEALTH` only after a future implementation module exists.

PASS means the contract surface preserves the failure-learning boundary.
PASS does not mean strategy acceptance, deployment readiness, broker truth
completion, live-source readiness, paper-order permission, live-order
permission, or real-capital permission.

