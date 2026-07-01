# Validation Results - TASK-4105

| Command | Result | Notes |
|---|---|---|
| python scripts/ops/build_context_bundle.py --task TASK-4105 | PASS | 1793 approximate tokens |
| python scripts/ops/validate_context_bundle.py --task TASK-4105 | PASS | 1793/22000 tokens |
| python scripts/ops/validate_prompt_regression.py | PASS | 4 prompt regression cases pass |
| python scripts/ops/validate_task_scope.py --task TASK-4105 | PASS_WITH_WARNINGS | Existing dirty worktree outside TASK-4105 manifest ignored |
| python scripts/ops/validate_codex_closeout.py --task TASK-4105 | PASS_WITH_WARNINGS | Closeout passes with inherited doc soft-mode and dirty-worktree warnings |
