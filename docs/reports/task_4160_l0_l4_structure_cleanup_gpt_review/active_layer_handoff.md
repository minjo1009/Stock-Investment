# TASK-4160 Active L0-L4 Layer Handoff

## Purpose

This is the active read-first handoff for Layer 0 through Layer 4 structure cleanup.

It does not move, rename, delete, or refactor existing code. It only fixes project navigation by naming current active entrypoints, validators, reports, and forbidden interpretations.

## Hard State

| Boundary | Status |
|---|---|
| Strategy | NOT_ACCEPTED |
| Deployment | DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY |
| Real capital | FORBIDDEN |
| Broker mutation | FORBIDDEN |
| Live order | FORBIDDEN |
| Paper promotion | FORBIDDEN |
| Missing/stale/incomplete data | UNKNOWN/BLOCKER, never negative evidence |

## Current L0 Runtime State

| Item | Current interpretation |
|---|---|
| Public newswire backfill | RUNNING |
| Current control task | TASK-4159 |
| Worker posture | BusinessWire 2 / GlobeNewswire 1 / PRNewswire 1 until controller allows promotion |
| BusinessWire | Long-tail bottleneck |
| GlobeNewswire | Monthly shards are usually short; remaining total work can still take hours |
| PRNewswire | Unit completion slow but row/offset progress exists; range split remains prohibited |
| BW4 promotion | Controlled by `controlled_acceleration_decision.json`; no automatic apply without explicit operator action |

## Layer Ownership Matrix

| Layer | Owns | Must not own |
|---|---|---|
| L0 | raw collection, backfill, runtime collectors, scheduler proof, raw integrity, source runtime status | feature scoring, thesis, ranking, order intent |
| L1 | source packets, raw lineage, raw hash/path, source time, available-to-brain time, ticker/entity mapping status, blocker status | event scoring, alpha, ranking, trading signal |
| L2 | event primitive/admission views, diagnostic feature candidates, dedup, stale/effect-window metadata, L3-readable handoff | final signal, order, sizing, paper/live eligibility |
| L3 | relation graphs, event clusters, relation quality, coverage gaps, diagnostic strategy view | final thesis acceptance, graph-count-as-quality, trading decisions |
| L4 | diagnostic thesis bundles, evidence links, lineage checks, blocker/contradiction visibility, review status | buy/sell/hold, ranking, sizing, order, broker, paper/live, deployment readiness |

## Read Order For Future Codex Runs

1. `AGENTS.md`
2. `ops/task_registry.yaml`
3. `ops/doc_registry.yaml`
4. This file.
5. `docs/reports/task_4160_l0_l4_structure_cleanup_gpt_review/active_layer_manifest.json`
6. The latest task report for the layer being edited.
7. The exact script or validator being edited.

## Active L0 Entrypoints

| Role | Path |
|---|---|
| Public newswire sharded backfill launcher | `scripts/run_l0_public_newswire_sharded_backfill.py` |
| Public newswire aggregate | `scripts/aggregate_l0_public_newswire_shards.py` |
| Public newswire validator | `scripts/validate_l0_public_newswire_sharded_backfill.py` |
| Public newswire controlled acceleration controller | `scripts/control_l0_public_newswire_acceleration.ps1` |
| Public newswire monitor | `scripts/run_l0_public_newswire_sharded_progress_monitor.ps1` |
| Public newswire shard inventory helpers | `tools/db/source_acquisition/public_newswire_shards.py` |
| Public newswire collector | `tools/db/source_acquisition/public_newswire_collector.py` |
| TASK-4159 report | `docs/reports/task_4159_l0_public_newswire_controlled_acceleration/report.md` |

## Active L1 Entrypoints

| Role | Path |
|---|---|
| L1 source packet bootstrap | `scripts/build_l1_source_packet_bootstrap.py` |
| L1 source packet validator | `scripts/validate_l1_source_packet_bootstrap.py` |
| L1 data-present hardening | `scripts/run_l1_data_present_hardening.py` |
| L1 data-present validator | `scripts/validate_l1_data_present_hardening.py` |
| L1 practical hardening | `scripts/run_l1_practical_hardening_4138.py` |
| L1 practical hardening validator | `scripts/validate_l1_practical_hardening_4138.py` |
| L1/L2 compatibility bridge | `scripts/run_l1_l2_compatibility_4144.py` |
| L1/L2 compatibility validator | `scripts/validate_l1_l2_compatibility_4144.py` |
| L1 bootstrap helper | `tools/db/source_acquisition/l1_bootstrap.py` |

## Active L2 Entrypoints

| Role | Path |
|---|---|
| L2 intake feature admission | `scripts/run_l2_intake_feature_admission.py` |
| L2 intake validator | `scripts/validate_l2_intake_feature_admission.py` |
| L2 swing news feature admission | `scripts/run_l2_swing_news_feature_admission_4140.py` |
| L2 swing news validator | `scripts/validate_l2_swing_news_feature_admission_4140.py` |
| L2 swing event admission | `scripts/run_l2_swing_event_admission_4142.py` |
| L2 swing event validator | `scripts/validate_l2_swing_event_admission_4142.py` |
| L2 completion/read contract | `scripts/run_l2_completion_4143.py` |
| L2 completion validator | `scripts/validate_l2_completion_4143.py` |
| L0-L2 wide handoff | `scripts/run_l0_l2_wide_handoff_4146.py` |
| L0-L2 wide handoff validator | `scripts/validate_l0_l2_wide_handoff_4146.py` |
| L0-L2 hardening loop | `scripts/run_l0_l2_hardening_4147.py` |
| L0-L2 hardening validator | `scripts/validate_l0_l2_hardening_4147.py` |
| L0 news to L2 ingestion | `scripts/ingest_l0_news_to_l2.py` |
| Active safe realtime config | `configs/l0_realtime_operational_safe_config_4147.json` |

## Active L3 Entrypoints

| Role | Path |
|---|---|
| L3 diagnostic strategy view | `scripts/build_l3_diagnostic_strategy_view_4150.py` |
| L3 diagnostic strategy validator | `scripts/validate_l3_diagnostic_strategy_view_4150.py` |
| L3 relation graph v2 | `scripts/build_l3_relation_graph_v2_4152.py` |
| L3 relation graph v2 validator | `scripts/validate_l3_relation_graph_v2_4152.py` |
| L3 relation graph quality guard | `scripts/build_l3_relation_graph_quality_guard_4154.py` |
| L3 relation graph quality validator | `scripts/validate_l3_relation_graph_quality_guard_4154.py` |

## Active L4 Entrypoints

| Role | Path |
|---|---|
| L4 thesis bundle builder | `scripts/build_l4_thesis_bundles.py` |
| L4 thesis bundle validator | `scripts/validate_l4_thesis_bundle_package.py` |
| L4 goal definition review | `docs/reports/task_4155_l4_goal_definition_gpt_review/report.md` |
| L4 thesis bundle bootstrap | `docs/reports/task_4156_l4_thesis_bundle_bootstrap/report.md` |

## Active Report Families

| Layer | Current report directories |
|---|---|
| L0 | `docs/reports/task_4157_l0_public_newswire_sharded_backfill/`, `docs/reports/task_4158_l0_public_newswire_scheduler_repair/`, `docs/reports/task_4159_l0_public_newswire_controlled_acceleration/` |
| L1 | `docs/reports/task_4137_l1_1to6_gpt_pro_review/`, `docs/reports/task_4138_l1_practical_hardening/`, `docs/reports/task_4144_l1_l2_compatibility_bridge/` |
| L2 | `docs/reports/task_4141_l2_gpt_pro_design_review/`, `docs/reports/task_4142_l2_swing_event_admission/`, `docs/reports/task_4143_l2_completion_gpt_review_and_read_contract/`, `docs/reports/task_4146_l0_l2_wide_packetization_handoff/`, `docs/reports/task_4147_l0_l2_hardening_gpt_review_and_implementation/` |
| L3 | `docs/reports/task_4150_l3_diagnostic_strategy_view_bootstrap/`, `docs/reports/task_4153_l3_relation_graph_v2_gpt_review/`, `docs/reports/task_4154_l3_relation_graph_v2_quality_guard/` |
| L4 | `docs/reports/task_4155_l4_goal_definition_gpt_review/`, `docs/reports/task_4156_l4_thesis_bundle_bootstrap/` |

## Legacy And Dirty Worktree Rules

1. Do not delete, move, or rename dirty files during structure cleanup.
2. Do not treat old task reports as active unless they are listed in this handoff or explicitly referenced by `ops/doc_registry.yaml`.
3. Do not revive deleted legacy L2/L3 scripts without a dedicated recovery task.
4. Do not read the whole repository to decide current layer state.
5. Do not infer active status from filename alone; check this handoff, manifest, task registry, and doc registry.

## Explicit Do Not Do

| Do not do | Reason |
|---|---|
| Do not stop L0 backfill for structure cleanup | Backfill is live and diagnostic-only safe |
| Do not apply BW4 here | Runtime acceleration is controlled by TASK-4159 controller |
| Do not split PRNewswire ranges | Prohibited until PR is proven as real long-tail bottleneck |
| Do not convert L2 to final signal store | L2 remains diagnostic/admission/primitive |
| Do not use L3 graph count as quality | Count inflation is not evidence quality |
| Do not make L4 institutional PASS | L4 is diagnostic bundle/review infrastructure |
| Do not add broker/order/paper/live paths | Hard state forbids it |

## Validation Checklist

Run only validators relevant to the files touched:

1. `python -m json.tool docs/reports/task_4160_l0_l4_structure_cleanup_gpt_review/active_layer_manifest.json`
2. `python scripts/validate_l0_public_newswire_sharded_backfill.py --shard-artifact-root data/artifacts/l0_public_newswire_backfill_shards --shard-raw-root data/raw/l0_public_newswire_backfill_shards --inventory-path data/artifacts/l0_public_newswire_backfill_shards/shard_inventory.json --aggregate-progress data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json`
3. `python -m unittest tests.test_l0_public_newswire_sharded_backfill`
4. `python scripts/ops/validate_task_registry.py`
5. `python scripts/ops/validate_doc_registry.py --soft`
6. `python scripts/ops/validate_task_scope.py --task TASK-4160`
7. `python scripts/ops/validate_required_artifacts.py --task TASK-4160`
8. `python scripts/ops/validate_codex_closeout.py --task TASK-4160`
