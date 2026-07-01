# GPT Pro Review Prompt: TASK-4156 L4 Diagnostic Thesis Bundle Bootstrap

You are reviewing a local working copy that may not be fully reflected in GitHub.

Act as:

1. Professional Backend Engineer
2. Quant Data Infrastructure Reviewer
3. Institutional Equity Research PM
4. Systematic PM / Trading Research Reviewer
5. Risk and Trading Controls Reviewer

Use the local implementation summary below as the source of truth. Do not assume GitHub contains the latest L0-L4 work.

## Original User Goal

Implement Layer 4 based on prior GPT Pro design discussion, and develop it through staged GPT review loops.

## Project Hard State

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data is `UNKNOWN/BLOCKER`, never negative evidence
- L4 must not produce final policy actions, order intent, sizing, ranking, live/paper eligibility, broker mutation, strategy acceptance, or deployment readiness.

## Prior GPT Pro Design Verdict

TASK-4155 verdict was `CONDITIONAL PASS`.

The approved L4 bootstrap scope was:

- diagnostic thesis bundle only
- deterministic builder
- evidence lineage table
- blocker table
- run manifest
- semantic validator
- tests
- no graph DB
- no vector DB
- no LLM thesis writer
- no ranking engine
- no broker integration
- no scheduler
- no UI

## Codex Implementation Result

Implemented:

- `configs/l4_thesis_bundle_4156.json`
- `src/brain/l4_thesis_bundle/__init__.py`
- `src/brain/l4_thesis_bundle/schema.py`
- `src/brain/l4_thesis_bundle/builder.py`
- `src/validation/l4_thesis_bundle_validator.py`
- `scripts/build_l4_thesis_bundles.py`
- `scripts/validate_l4_thesis_bundle_package.py`
- `tests/test_l4_thesis_bundle_package.py`

Generated artifacts:

- `data/diagnostics/l4/l4_thesis_bundles.jsonl`
- `data/diagnostics/l4/l4_thesis_evidence_links.csv`
- `data/diagnostics/l4/l4_thesis_blockers.csv`
- `data/diagnostics/l4/l4_run_manifest.json`
- `data/diagnostics/l4/l4_validation_report.json`

## Source Inputs Used

- L1 article packets: `data/artifacts/task_4147_l0_l2_hardening_gpt_review_and_implementation/l1_article_packets.csv`
- L2 article features: `data/artifacts/task_4147_l0_l2_hardening_gpt_review_and_implementation/l2_diagnostic_feature_rows.csv`
- L1 wide packets: `data/artifacts/task_4146_l0_l2_wide_packetization_handoff/l1_wide_normalized_source_packets.csv`
- L2 wide candidates: `data/artifacts/task_4146_l0_l2_wide_packetization_handoff/l2_feature_materialization_candidates.csv`
- L3 relation graphs: `data/artifacts/task_4152_l3_relation_graph_v2/l3_relation_graphs.csv`
- L3 relation edges: `data/artifacts/task_4152_l3_relation_graph_v2/l3_relation_edges.csv`
- L3 coverage gaps: `data/artifacts/task_4152_l3_relation_graph_v2/l3_coverage_gaps.csv`
- L3 quality guard handoff: `data/artifacts/task_4154_l3_relation_graph_v2_quality_guard/l3_l4_diagnostic_handoff_manifest.json`
- L0 collection status: `data/artifacts/l0_collection_status/current_status.json`

## Generated Counts

- L4 thesis bundles: 5,398
- L4 evidence links: 7,150
- L4 blockers: 20,079

Bundle status:

- `DRAFT_BLOCKED`: 2
- `DRAFT_MIXED`: 5,396

Institutional quality status:

- `BLOCKED`: 2
- `MIXED`: 5,396

Thesis type:

- `COVERAGE_GAP`: 2
- `ENTITY_EVENT`: 2,718
- `MACRO_CONTEXT`: 828
- `SOURCE_EVENT_PROTO`: 1,850

Coverage status:

- `BLOCKED`: 2
- `INCOMPLETE`: 5,396

Relation quality status:

- `BLOCKED`: 2
- `MIXED`: 436
- `SPARSE`: 3,110
- `PROTO`: 1,850

## Validation Results

Commands passed:

```text
python -m py_compile src/brain/l4_thesis_bundle/schema.py src/brain/l4_thesis_bundle/builder.py src/validation/l4_thesis_bundle_validator.py scripts/build_l4_thesis_bundles.py scripts/validate_l4_thesis_bundle_package.py
python -m unittest tests.test_l4_thesis_bundle_package
python scripts/build_l4_thesis_bundles.py --config configs/l4_thesis_bundle_4156.json
python scripts/validate_l4_thesis_bundle_package.py --artifact-dir data/diagnostics/l4
```

Validator result:

```text
TASK-4156 PASS
passes=12
failures=0
```

Validator confirmed:

- required L4 artifacts exist
- bundle/evidence/blocker schemas are present
- hard boundaries remain valid
- negative evidence is forbidden
- raw-only support/context evidence is blocked
- manifest counts reconcile
- bundle/evidence/blocker semantic consistency is valid

## Review Questions

Please review whether this L4 implementation satisfies the prior TASK-4155 design.

Specifically answer:

1. PASS / FAIL / BLOCKED / CONDITIONAL PASS
2. P0 issues that must be patched before closeout
3. P1 issues that should be patched now if small and high-value
4. P2 issues to defer
5. Whether the implementation overclaims trading authority anywhere
6. Whether `DRAFT_MIXED` for non-coverage bundles is acceptable given `CONTRADICTION_NOT_SCANNED` blockers
7. Whether `coverage_status=INCOMPLETE` for most bundles is the correct conservative handling while L0 backfill is incomplete
8. Whether any additional validator rule is required now
9. Exact Codex patch prompt for P0/P1 only

Do not recommend:

- graph DB
- vector DB
- LLM thesis writer
- ranking
- BUY/SELL/HOLD
- order intent
- sizing
- broker integration
- paper/live readiness
- strategy acceptance
- deployment readiness
- UI
- scheduler

