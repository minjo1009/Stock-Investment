# Task Registry Contract

## Purpose

The task registry is the project control plane.

Every active or canonical task must say:

- what it owns
- what it produced
- whether it is accepted
- whether it is deployable
- which artifacts are safe to commit
- which artifacts are local-only

## Required Fields

The current `tasks/task_registry.csv` fields remain valid:

```text
task_id,title,owner_team,status,canonical_state,strategy_acceptance,data_readiness,parent_task,key_report,key_decision,key_artifacts,validation_command,notes
```

For new rows, `notes` must include one of these commit states:

```text
commit_state=code_ready
commit_state=summary_only
commit_state=artifact_local_only
commit_state=blocked_cleanup_needed
```

## Status Meaning

| Field | Allowed Meaning |
| --- | --- |
| `status=Accepted` | Strategy or infrastructure result is accepted under the task's stated validation scope. |
| `status=Diagnostic Only` | Research output only. No deployment or capital implication. |
| `canonical_state=canonical` | Current preferred implementation or contract for that domain. |
| `canonical_state=active` | Current working line, not necessarily accepted. |
| `canonical_state=diagnostic` | Historical or investigative task. |
| `strategy_acceptance=diagnostic-only` | No strategy acceptance. |
| `strategy_acceptance=raw-ready` | Raw source readiness only. |

## Artifact Commit Rules

Commit by default:

- `src/**/*.py`
- `tests/**/*.py`
- small `docs/**/*.md`
- task decision CSVs
- pass/fail CSVs
- artifact manifests

Do not commit by default:

- `data/raw/**`
- `data/artifacts/**`
- large `docs/reports/**/*.csv`
- `docs/reports/**/*.jsonl`
- runtime databases
- broker/account archives

## Brain Layer Rule

Brain layer tasks must identify their layer in `notes`:

```text
brain_layer=source_evidence
brain_layer=primitive_fact
brain_layer=economic_meaning
brain_layer=relation_edge
brain_layer=candidate_bundle
brain_layer=slot_decision
brain_layer=qa_resolver
```

No task may claim deployment readiness unless:

1. leakage audit passed
2. cost/slippage treatment passed when PnL is involved
3. split/OOS passed when strategy claims are involved
4. raw source readiness passed when live or replay claims are involved
5. artifact manifest exists

## Current Cleanup Decision

Task727 through Task742 should be treated as review-only brain research until a smaller canonical subset is selected.

Task742 is the current practical economic meaning candidate, but it is not a trading signal and not a backtest permission gate.
