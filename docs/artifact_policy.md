# Artifact Lifecycle Policy

## Goal

Keep reports readable, keep large panels reproducible, and prevent `docs/reports` from becoming unmanaged data storage.

## Artifact Classes

| Class | Location | Examples |
|---|---|---|
| Report | `docs/reports/<task_id>/` | Markdown report, decision CSV, manifest |
| Derived panel | `data/artifacts/<task_id>/` | assignment panels, grid candidate pools |
| Raw source | `data/raw/<source>/` | bars, quotes, stream archive |
| Archived report | `archive/reports/<task_id>/` | superseded historical reports |

## Status Values

- `canonical`: current source of truth for a layer
- `active`: current working artifact
- `diagnostic`: useful research result, not accepted strategy
- `superseded`: replaced by a later task
- `archived`: preserved but excluded from default workflows

## Rules

- Large CSV panels should not be added to `docs/reports` for new tasks.
- Existing large report artifacts must receive a manifest before moving.
- Deletion requires explicit approval.
- Every canonical task must have a registry row and an artifact manifest.
- Reports must link to large artifacts instead of embedding them.

## First Migration Target

Start with manifest-only classification for the largest historical directories:

- `task_406_deterministic_decision_rebuild`
- `task_401_forward_live_canonical_multifactor_decision_layer`
- `task_407_raw_native_vectorized_rebuild`
- `task_406_raw_factor_source_audit`
- `task_399_intraday_universe_history_expansion`

Do not move these until registry coverage is complete.
