# Delete Candidate Policy

Deletion must be conservative but real.

## A001 Rule

A001 does not delete files. It only writes `docs/reports/A001_project_management_reset/delete_candidates.csv`.

## Candidate Columns

```csv
path,category,reason,evidence,referenced_by,delete_risk,recommendation,requires_user_approval
```

Allowed recommendations:

- `DELETE_SAFE`
- `ARCHIVE_ONLY`
- `KEEP`
- `NEEDS_REVIEW`

## Potentially Safe Categories

- duplicate temporary screenshots
- obsolete local review snapshots
- generated cache files with reproducible generators
- empty folders
- stale intermediate GPT loop dumps if summarized elsewhere
- duplicate copied prompts/responses where final report exists
- dead PWA/old UI evidence if superseded and not referenced

## Never Mark As DELETE_SAFE

- `tasks/task_registry.csv`
- `docs/ownership/current_operating_model.md`
- `AGENTS.md`
- `README.md`
- active SSOT docs
- strategy/deployment/acceptance contracts
- validators
- raw source data
- DB authority files
- artifact manifests
- canonical task reports
- reports that prove status boundaries
- files needed to prove `NOT_ACCEPTED`, `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`, or `FORBIDDEN`

## Approval Gate

Every delete action requires user approval, even when the A001 recommendation is `DELETE_SAFE`.

