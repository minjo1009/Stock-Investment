# GPT Pro Prompt: TASK-4160 L0-L4 Structure Cleanup Review

You are reviewing a local working copy that is not fully reflected in GitHub.

Do not rely on GitHub as the latest source of truth. Use the local context packet below as the latest state. You may use GitHub only for broad project context if available, but do not override the local packet with stale GitHub state.

Act as:

1. Professional Backend Engineer
2. Data Platform Architect
3. Quant Data Infrastructure Reviewer
4. Systematic PM / Trading Research Reviewer

Project hard state:

- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data is UNKNOWN/BLOCKER, never negative evidence
- No BUY/SELL/ranking/sizing/order/paper/live/deployment recommendation.

User goal:

The user wants Codex to do structure cleanup for Layer 0 through Layer 4 while L0 public newswire backfill continues. The cleanup should reduce project confusion and make it clear which layer owns which artifacts, validators, handoff files, and status reports.

Important: Avoid over-engineering. Do not recommend code for code's sake, guardrails for guardrails' sake, or large framework migrations. Recommend only changes with direct practical value.

## Current Local State

### L0 public newswire backfill

- TASK-4159 implemented controlled acceleration.
- Current aggregate status: RUNNING.
- Current progress: about 47.6%.
- Completed units: 1,953 / 4,101.
- Pending units: 2,148.
- Current workers: BusinessWire 2, GlobeNewswire 1, PRNewswire 1.
- Safety flags are all closed: broker/order/live/paper/real-capital/trade-authority all 0.
- BusinessWire remains the long-tail bottleneck.
- GlobeNewswire is not a one-month/two-hour bottleneck. Typical GN monthly shard takes about 1.5 minutes, but the whole remaining GN set still takes time because many monthly shards remain.
- PRNewswire unit completion is slow, but row/offset progress is observed. PRNewswire offset/range split remains prohibited for now.

### TASK-4159 implemented

Files:

- `scripts/run_l0_public_newswire_sharded_backfill.py`
- `scripts/aggregate_l0_public_newswire_shards.py`
- `scripts/validate_l0_public_newswire_sharded_backfill.py`
- `scripts/control_l0_public_newswire_acceleration.ps1`
- `scripts/run_l0_public_newswire_sharded_progress_monitor.ps1`
- `tests/test_l0_public_newswire_sharded_backfill.py`
- `docs/reports/task_4159_l0_public_newswire_controlled_acceleration/*`

Capabilities:

- source base lanes and caps.
- dynamic lane rebalance.
- source-specific budgets/runtime.
- progress-aware stale detection using completed unit, active offset, row count, raw bytes, last successful fetch.
- dead RUNNING lock recovery.
- live lock skip defense.
- source-level ETA and active/partial/stale worker aggregate fields.
- validator for dead PID, active offset completed misclassification, aggregate fields, safety flags.
- hourly monitor writes `controlled_acceleration_decision.json`.

Current controller decision:

```text
decision: BW4_BLOCKED
reason: globenewswire_not_complete,stable_minutes_below_threshold
validator_passed: true
safety_closed: true
```

### L1

Known L1 direction from recent tasks:

- L1 should be row/article-level packetization, not only batch-level.
- News, macro, public newswire must remain swing/daily trading feature candidates, not "not feature forever".
- L1 must preserve source lineage, raw path/hash, source time, available-to-brain time, mapping status, blocker status.
- Data missing because L0 is still backfilling is UNKNOWN/BLOCKER, not negative evidence.
- L1 validation should keep running and should not block just because L0 coverage is incomplete.

Important local summary:

```json
{
  "task_id": "TASK-4138",
  "source_family_policy_rows": 5,
  "validation_runs": 3,
  "validation_failures": [],
  "trading_authority_opened": false,
  "paper_live_broker_order_opened": false,
  "feature_allowed_now_rows": []
}
```

### L2

Known L2 direction:

- L2 is not final signal/scoring/order logic.
- L2 should convert L1 packets into safe swing event primitive/admission/read views.
- News, macro, public newswire are feature candidates, but materialization remains diagnostic and gated.
- L2 must separate existing legacy news code from the new L2 event/primitive pipeline.
- L2 must dedup repeated source events, map entity/ticker/source family, keep stale/effect-window metadata, and pass to L3.

Important local TASK-4147 summary:

```json
{
  "task_id": "TASK-4147",
  "l1_article_packets": 1093,
  "l1_article_ready_packets": 1093,
  "raw_article_packet_blockers": 0,
  "newswire_mapping_queue_rows": 407,
  "newswire_l0_mapped_rows": 8253,
  "l2_diagnostic_feature_rows": 1842,
  "critical_incomplete_dead_backfill_lanes": [],
  "separated_realtime_config": "configs/l0_realtime_operational_safe_config_4147.json",
  "scheduler_task_name": "TraderBrainL0L2Hardening4147",
  "trading_eligible_rows": 0,
  "signal_order_export_allowed_rows": 0,
  "broker_mutation_permitted_rows": 0
}
```

### L3

Known L3 direction:

- L3 should build relation graphs, event clusters, coverage gaps, relation quality, and diagnostic strategy view.
- L3 must not treat graph count as evidence quality.
- L3 must not convert diagnostic relations into trading signals.
- L3 v2 increased relation graph coverage materially, but still has quality/coverage caveats.

Known artifacts/scripts:

- `scripts/build_l3_diagnostic_strategy_view_4150.py`
- `scripts/build_l3_relation_graph_v2_4152.py`
- `scripts/build_l3_relation_graph_quality_guard_4154.py`
- corresponding validators.

### L4

Known L4 direction:

- L4 is diagnostic thesis bundle assembly, not final institutional thesis acceptance.
- L4 should connect L0-L3 evidence, lineage, relation graph, coverage gap, contradiction status, and blocker status into reviewable thesis bundles.
- L4 must not produce buy/sell/hold/ranking/sizing/order/paper/live/deployment readiness.

Known scripts:

- `scripts/build_l4_thesis_bundles.py`
- `scripts/validate_l4_thesis_bundle_package.py`

### Current problem to solve

The project now has many task-specific scripts and reports:

- L0 task scripts and validators.
- L1 packet scripts and validators.
- L2 admission/materialization scripts and validators.
- L3 relation graph scripts and validators.
- L4 thesis bundle scripts and validators.
- Many old/dirty files in the worktree.

This makes it easy for future Codex runs to read the wrong file, treat superseded reports as active, or confuse legacy L2/news code with current L2 event primitive/admission pipeline.

## What Codex wants from GPT

Please review and propose a concrete, low-overhead structure cleanup plan.

Focus on:

1. Which small set of current L0-L4 files should be treated as active entrypoints.
2. Which files should be indexed in a single handoff manifest or README so future Codex reads the right files first.
3. Whether we need a layer ownership matrix such as:
   - L0: collectors/backfill/scheduler/raw integrity
   - L1: source packets/lineage/mapping/blockers
   - L2: event primitive/admission/materialization candidates
   - L3: relation graph/event clusters/quality/coverage gaps
   - L4: thesis bundle/review blockers
4. Whether to create one `docs/reports/task_4160_l0_l4_structure_cleanup/active_layer_handoff.md` and one machine-readable `active_layer_manifest.json`.
5. How to avoid touching huge amounts of dirty/unrelated files.
6. What validators should be run after the cleanup.
7. What should explicitly NOT be done now.

Expected output:

1. Verdict: PASS / CONDITIONAL PASS / FAIL.
2. Prioritized structure cleanup plan.
3. Exact files Codex should create or edit.
4. Exact files Codex should avoid.
5. Validator checklist.
6. Korean plain-language summary suitable for the user.
