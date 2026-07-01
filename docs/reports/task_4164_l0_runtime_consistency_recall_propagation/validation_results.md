# TASK-4164 Validation Results

## Commands

```powershell
python -m py_compile scripts/run_l0_backfill_worker_recovery_4148.py scripts/run_l0_public_newswire_sharded_backfill.py scripts/aggregate_l0_public_newswire_shards.py scripts/reclassify_l0_public_newswire_recall_4163.py scripts/validate_l0_public_newswire_recall_4163.py
```

Result: PASS

```powershell
python scripts/validate_l0_public_newswire_recall_4163.py --artifact-dir data/artifacts/task_4164_l0_runtime_consistency_recall_propagation/businesswire --expected-task-id TASK-4164
```

Result: PASS

- processed_files=873
- recall_review_rows=10726
- status_changed_rows=9130
- overlay_rows_sampled=10726
- ENTITY_CANDIDATE_REVIEW present

```powershell
python scripts/validate_l0_public_newswire_recall_4163.py --artifact-dir data/artifacts/task_4164_l0_runtime_consistency_recall_propagation/prnewswire --expected-task-id TASK-4164
```

Result: PASS

- processed_files=95
- recall_review_rows=3516
- status_changed_rows=2595
- overlay_rows_sampled=3516
- ENTITY_CANDIDATE_REVIEW present

```powershell
python scripts/validate_l0_public_newswire_recall_4163.py --artifact-dir data/artifacts/task_4163_gn_filtering_recall_audit --expected-task-id TASK-4163
```

Result: PASS

- processed_files=330
- recall_review_rows=12040
- status_changed_rows=10225
- overlay_rows_sampled=12040
- ENTITY_CANDIDATE_REVIEW present

```powershell
python scripts/aggregate_l0_public_newswire_shards.py --skip-raw-dedupe
python scripts/validate_l0_public_newswire_sharded_backfill.py
```

Result: PASS with warnings

- WARN l1_unclassified_or_pending_count > 0
- WARN failed shards represented: 11

## Notes

The warnings are expected for an in-progress L0 backfill. They are not trading evidence and do not open any downstream authority.
