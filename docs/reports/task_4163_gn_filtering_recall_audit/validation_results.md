# TASK-4163 Validation Results

## Commands

```text
python -m pytest tests/test_l0_public_newswire_collector.py -q
```

Result: passed, 25 tests.

```text
python -m py_compile tools/db/source_acquisition/public_newswire_collector.py tools/db/source_acquisition/news_background_collector.py scripts/run_l0_l2_wide_handoff_4146.py scripts/reclassify_l0_public_newswire_recall_4163.py scripts/validate_l0_public_newswire_recall_4163.py
```

Result: passed.

```text
python scripts/validate_l0_public_newswire_recall_4163.py
```

Result: passed.

Validator output:

```json
{
  "failures": [],
  "passes": [
    "processed_files=330",
    "recall_review_rows=12040",
    "status_changed_rows=10225",
    "overlay_rows_sampled=12040",
    "ENTITY_CANDIDATE_REVIEW present"
  ],
  "warnings": []
}
```

```text
python scripts/ops/validate_task_registry.py
python scripts/ops/validate_doc_registry.py --soft
python scripts/ops/validate_required_artifacts.py --task TASK-4163
python scripts/ops/validate_task_scope.py --task TASK-4163
python scripts/ops/validate_codex_closeout.py --task TASK-4163
```

Result:

- task registry: passed
- doc registry: passed
- required artifacts: passed
- task scope: passed with warning because existing dirty files outside this task manifest were ignored
- closeout: passed with same scope warning
