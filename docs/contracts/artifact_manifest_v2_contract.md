# Artifact Manifest V2 Contract

V2 extends the existing artifact manifest without breaking old manifests.

Required fields:
- `relative_path`
- `artifact_class`
- `size_bytes`
- `sha256`
- `schema_version`
- `parent_artifact_id`
- `input_dataset_hash`
- `code_hash`
- `feature_list`
- `created_at_utc`
- `owner_team`
- `reviewer_team`
- `data_readiness`
- `strategy_acceptance`

Large panels must live under `data/artifacts/<task_id>/`; reports should link through manifest rows.