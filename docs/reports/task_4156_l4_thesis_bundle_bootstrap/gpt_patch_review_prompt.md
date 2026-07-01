# GPT Pro Patch Review Prompt: TASK-4156 L4 P1 Semantic Guard Hardening

You previously reviewed TASK-4156 and returned:

```text
TASK-4156 = CONDITIONAL PASS
P0 = none
P1 = semantic validator hardening required before clean closeout
```

Codex implemented the P1 patch.

## Hard State

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data is `UNKNOWN/BLOCKER`, never negative evidence
- L4 remains diagnostic-only

## P1 Patch Implemented

Changed files:

- `src/brain/l4_thesis_bundle/schema.py`
- `src/brain/l4_thesis_bundle/builder.py`
- `src/validation/l4_thesis_bundle_validator.py`
- `tests/test_l4_thesis_bundle_package.py`

Patch summary:

1. Added exact forbidden downstream authority fields:
   - `recommendation`
   - `policy_action`
   - `final_score`
   - `target_weight`
   - `position_size`
   - `quantity`
   - `broker_order_id`
   - `paper_eligible`
   - `live_eligible`
   - `deployment_ready`
   - `strategy_accepted`

2. Added manifest `source_inputs` fingerprints:
   - `role`
   - `path`
   - `exists`
   - `row_count` for CSV/JSONL
   - `sha256`
   - `mtime_utc`

3. Added validator rules:
   - If a bundle has `CONTRADICTION_NOT_SCANNED`, then:
     - `bundle_status` must be `DRAFT_MIXED` or `DRAFT_BLOCKED`
     - `institutional_quality_status` must be `MIXED` or `BLOCKED`
     - `coverage_status` must be `INCOMPLETE` or `BLOCKED`
   - Exact final/ready/actionable/eligible status values are rejected for status fields when contradiction is not scanned.
   - If L0 coverage is incomplete, L4 `coverage_status` may not be `COMPLETE`, `FULL`, `READY`, or `ACCEPTED`.
   - Manifest source inputs must include existing paths, non-empty sha256, mtime, and non-negative row counts for CSV/JSONL.
   - Generated artifact counts must still reconcile.

4. Added focused tests:
   - contradiction-not-scanned rejects complete coverage state
   - L0 incomplete state rejects complete coverage state
   - manifest source input sha256 is required
   - downstream authority fields are rejected
   - existing diagnostic happy path still passes

## Validation Commands

All passed:

```text
python -m py_compile src/brain/l4_thesis_bundle/schema.py src/brain/l4_thesis_bundle/builder.py src/validation/l4_thesis_bundle_validator.py scripts/build_l4_thesis_bundles.py scripts/validate_l4_thesis_bundle_package.py
python -m unittest tests.test_l4_thesis_bundle_package
python scripts/build_l4_thesis_bundles.py --config configs/l4_thesis_bundle_4156.json
python scripts/validate_l4_thesis_bundle_package.py --artifact-dir data/diagnostics/l4
```

Current result:

```text
tests: 8 passed
TASK-4156 L4 validator: PASS passes=13 failures=0
```

## Review Request

Please answer concisely:

1. PASS / FAIL / BLOCKED / CONDITIONAL PASS after P1 patch
2. Any remaining P0 issue?
3. Any remaining P1 issue that must be patched before TASK-4156 closeout?
4. Are P2 items safe to defer?
5. Is the closeout acceptable under diagnostic-only hard boundaries?

Do not recommend new broad scope such as graph DB, vector DB, LLM thesis writer, ranking, order intent, sizing, broker integration, paper/live readiness, strategy acceptance, deployment readiness, UI, or scheduler.

